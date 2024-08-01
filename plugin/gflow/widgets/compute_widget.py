import datetime
import subprocess
from pathlib import Path
from typing import NamedTuple, Tuple, Union

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from qgis.core import (
    Qgis,
    QgsApplication,
    QgsMapLayerProxyModel,
    QgsProject,
    QgsRasterLayer,
    QgsTask,
)
from qgis.gui import QgsMapLayerComboBox

from gflow.core import layer_styling
from gflow.core.processing import (
    raster_contours,
)
from gflow.core.extract import extraction_to_layers


class OutputOptions(NamedTuple):
    raster: bool
    mesh: bool
    contours: bool
    piezometer: bool
    gage: bool
    lake_stage: bool
    discharge: bool
    flux_inspector: bool
    pathlines: bool
    spacing: float


class ComputeTask(QgsTask):
    def __init__(self, parent, data, message_bar):
        super().__init__(self.task_description, QgsTask.CanCancel)
        self.parent = parent
        self.data = data
        self.message_bar = message_bar
        self.exception = None
        self.response = None
        self.starttime = None

    @property
    def task_description(self):
        return "GFLOW computation"

    def run(self):
        self.starttime = datetime.datetime.now()
        try:
            gflow_path = self.data["gflow_path"]
            path = self.data["path"]
            process = subprocess.Popen(
                [gflow_path, path.name],
                cwd=path.parent,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            process.communicate()
            return True

        except Exception as exception:
            self.exception = exception
            return False

    def success_message(self):
        runtime = datetime.datetime.now() - self.starttime
        hours, remainder = divmod(runtime.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        return (
            f"GFLOW computation completed in: {hours} hours, {minutes} minutes, "
            f"and {round(seconds, 2)} seconds."
        )

    def push_success_message(self) -> None:
        self.message_bar.pushMessage(
            title="Info",
            text=self.success_message(),
            level=Qgis.Info,
        )
        return

    def push_failure_message(self) -> None:
        if self.exception is not None:
            message = "Exception: " + str(self.exception)
        elif self.response is not None:
            message = "Response: " + self.response
        else:
            message = "Unknown failure"

        self.message_bar.pushMessage(
            title="Error",
            text=f"Failed {self.task_description}. Server error:\n{message}",
            level=Qgis.Critical,
        )
        return

    def finished(self, result):
        self.parent.set_interpreter_interaction(True)
        if result:
            self.push_success_message()
            path = self.data["path"]
            output = self.data["output_options"]
            name = f"{Path(path).stem}"
            self.parent.parent.create_output_group(name=f"{name} output")
            if output.raster:
                self.parent.load_raster_result(path, output.contours)
            if output.pathlines:
                self.parent.load_pathlines_result(path)
            self.parent.load_extract_result(path)

        else:
            self.push_failure_message()
        return

    def cancel(self) -> None:
        self.parent.set_interpreter_interaction(True)
        super().cancel()
        return


class ComputeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.compute_task = None
        self.start_task = None
        self.parent = parent

        self.domain_button = QPushButton("Set to current extent")
        self.compute_button = QPushButton("Compute")
        self.compute_button.clicked.connect(self.compute)

        self.mesh_checkbox = QCheckBox("Mesh")
        self.raster_checkbox = QCheckBox("Raster")
        self.contours_checkbox = QCheckBox("Contours")
        self.piezometer_checkbox = QCheckBox("Piezometer")
        self.gage_checkbox = QCheckBox("Gage")
        self.lake_stage_checkbox = QCheckBox("Lake Stage")
        self.discharge_checkbox = QCheckBox("Discharge")
        self.flux_inspector_checkbox = QCheckBox("Flux Inspector")
        self.pathlines_checkbox = QCheckBox("Pathlines")

        self.spacing_spin_box = QDoubleSpinBox()
        self.spacing_spin_box.setMinimum(0.0)
        self.spacing_spin_box.setMaximum(10_000.0)
        self.spacing_spin_box.setSingleStep(1.0)
        self.domain_button.clicked.connect(self.domain)
        # By default: all output
        self.mesh_checkbox.toggled.connect(self.contours_checkbox.setEnabled)
        self.mesh_checkbox.toggled.connect(
            lambda checked: not checked and self.contours_checkbox.setChecked(False)
        )

        # self.mesh_checkbox = QCheckBox("Trimesh")
        self.output_line_edit = QLineEdit()
        self.output_button = QPushButton("Set path as ...")
        self.output_button.clicked.connect(self.set_output_path)
        self.contour_button = QPushButton("Redraw contours")
        self.contour_button.clicked.connect(self.redraw_contours)
        self.contour_layer = QgsMapLayerComboBox()
        self.contour_layer.setFilters(
            QgsMapLayerProxyModel.MeshLayer | QgsMapLayerProxyModel.RasterLayer
        )
        self.contour_min_box = QDoubleSpinBox()
        self.contour_max_box = QDoubleSpinBox()
        self.contour_step_box = QDoubleSpinBox()
        self.contour_max_box.setMaximum(1000.0)
        # Ensure the maximum cannot dip below the min box value.
        self.contour_min_box.valueChanged.connect(self.set_minimum_contour_stop)
        self.contour_min_box.setMinimum(-1000.0)
        self.contour_min_box.setMaximum(1000.0)
        self.contour_step_box.setSingleStep(0.1)

        # Set default values
        self.reset()

        # Layout
        layout = QVBoxLayout()
        domain_group = QGroupBox("Domain")
        result_group = QGroupBox("Output")
        contour_group = QGroupBox("Contour")
        domain_layout = QVBoxLayout()
        result_layout = QVBoxLayout()
        contour_layout = QVBoxLayout()
        domain_group.setLayout(domain_layout)
        result_group.setLayout(result_layout)
        contour_group.setLayout(contour_layout)

        domain_row = QHBoxLayout()
        domain_row.addWidget(QLabel("Grid spacing"))
        domain_row.addWidget(self.spacing_spin_box)
        domain_layout.addWidget(self.domain_button)
        domain_layout.addLayout(domain_row)

        output_row = QHBoxLayout()
        output_row.addWidget(self.output_line_edit)
        output_row.addWidget(self.output_button)

        button_row = QHBoxLayout()
        button_row.addWidget(self.compute_button)
        result_layout.addLayout(output_row)

        result_layout.addWidget(self.mesh_checkbox)
        result_layout.addWidget(self.raster_checkbox)
        result_layout.addWidget(self.contours_checkbox)
        result_layout.addWidget(self.piezometer_checkbox)
        result_layout.addWidget(self.gage_checkbox)
        result_layout.addWidget(self.lake_stage_checkbox)
        result_layout.addWidget(self.discharge_checkbox)
        result_layout.addWidget(self.flux_inspector_checkbox)
        result_layout.addWidget(self.pathlines_checkbox)

        result_layout.addLayout(button_row)

        contour_row1 = QHBoxLayout()
        to_label = QLabel("to")
        to_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        step_label = QLabel("Step")
        step_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        contour_row1.addWidget(self.contour_min_box)
        contour_row1.addWidget(to_label)
        contour_row1.addWidget(self.contour_max_box)
        contour_row1.addWidget(step_label)
        contour_row1.addWidget(self.contour_step_box)
        contour_row2 = QHBoxLayout()
        contour_row2.addWidget(self.contour_layer)
        contour_row2.addWidget(self.contour_button)
        contour_layout.addLayout(contour_row1)
        contour_layout.addLayout(contour_row2)

        layout.addWidget(domain_group)
        layout.addWidget(result_group)
        layout.addWidget(contour_group)
        layout.addStretch()
        self.setLayout(layout)

    def reset(self):
        self.spacing_spin_box.setValue(25.0)
        self.output_line_edit.setText("")
        self.mesh_checkbox.setChecked(False)
        self.raster_checkbox.setChecked(True)
        self.contours_checkbox.setChecked(True)
        self.piezometer_checkbox.setChecked(False)
        self.gage_checkbox.setChecked(False)
        self.lake_stage_checkbox.setChecked(False)
        self.discharge_checkbox.setChecked(False)
        self.flux_inspector_checkbox.setChecked(False)
        self.pathlines_checkbox.setChecked(False)
        self.contour_min_box.setValue(-5.0)
        self.contour_max_box.setValue(5.0)
        self.contour_step_box.setValue(0.5)
        self.domain_button.setEnabled(False)
        self.compute_button.setEnabled(False)
        return

    def set_minimum_contour_stop(self) -> None:
        self.contour_max_box.setMinimum(self.contour_min_box.value() + 0.05)

    def set_interpreter_interaction(self, value: bool):
        self.parent.set_interpreter_interaction(value)

    def contour_range(self) -> Tuple[float, float, float]:
        return (
            float(self.contour_min_box.value()),
            float(self.contour_max_box.value()),
            float(self.contour_step_box.value()),
        )

    def add_contour_layer(self, layer) -> None:
        # Labeling
        labels = layer_styling.number_labels("head")
        # Renderer: simple black lines
        renderer = layer_styling.contour_renderer()
        self.parent.output_group.add_layer(
            layer, "vector", renderer=renderer, on_top=True, labels=labels
        )
        return

    @property
    def output_path(self) -> str:
        return self.output_line_edit.text()

    @property
    def output_options(self) -> OutputOptions:
        return OutputOptions(
            raster=self.raster_checkbox.isChecked(),
            mesh=self.mesh_checkbox.isChecked(),
            contours=self.contours_checkbox.isChecked(),
            piezometer=self.piezometer_checkbox.isChecked(),
            gage=self.gage_checkbox.isChecked(),
            lake_stage=self.lake_stage_checkbox.isChecked(),
            discharge=self.discharge_checkbox.isChecked(),
            flux_inspector=self.flux_inspector_checkbox.isChecked(),
            pathlines=self.pathlines_checkbox.isChecked(),
            spacing=self.spacing_spin_box.value(),
        )

    def clear_outdated_output(self, path: str) -> None:
        path = Path(path)
        gpkg_path = path.with_suffix(".output.gpkg")
        netcdf_paths = (path.with_suffix(".nc"), path.with_suffix(".ugrid.nc"))
        for layer in QgsProject.instance().mapLayers().values():
            source = layer.source()
            if (
                Path(source) in netcdf_paths
                or Path(source.partition("|")[0]) == gpkg_path
            ):
                QgsProject.instance().removeMapLayer(layer.id())
        return

    def redraw_contours(self) -> None:
        path = Path(self.output_path)
        layer = self.contour_layer.currentLayer()
        if layer is None:
            return

        start, stop, step = self.contour_range()
        if (start == stop) or (step == 0.0):
            return

        gpkg_path = str(path.with_suffix(".output.gpkg"))
        contours_name = "head-contours"

        layer = raster_contours(
            gpkg_path=gpkg_path,
            layer=layer,
            name=contours_name,
            start=start,
            stop=stop,
            step=step,
        )

        # Re-use layer if it already exists. Otherwise add a new layer.
        project_layers = {
            layer.name(): layer for layer in QgsProject.instance().mapLayers().values()
        }
        project_layer = project_layers.get(contours_name)
        if (
            (project_layer is not None)
            and (project_layer.name() == layer.name())
            and (project_layer.source() == layer.source())
        ):
            project_layer.reload()
        else:
            self.add_contour_layer(layer)
        return

    def set_output_path(self) -> None:
        current = self.output_path
        path, _ = QFileDialog.getSaveFileName(
            self, "Save output as...", current, "*.gpkg"
        )

        if path != "":  # Empty string in case of cancel button press
            self.output_line_edit.setText(str(Path(path).with_suffix("")))
            # Note: Qt does pretty good validity checking of the Path in the
            # Dialog, there is no real need to validate path here.
        return

    def set_default_path(self, text: str) -> None:
        """Called when different dataset path is chosen."""
        if text is None:
            return
        path = Path(text)
        self.output_line_edit.setText(str(path.parent / path.stem))
        return

    def compute(self) -> None:
        """
        Run a GFLOW computation with the current state of the currently active
        GeoPackage dataset.
        """
        directory = Path(self.output_path)
        directory.mkdir(parents=True, exist_ok=True)
        path = (directory / directory.stem).absolute().with_suffix(".dat")
        invalid_input = self.parent.dataset_widget.convert_to_gflow(path)
        # Early return in case some problems are found.
        if invalid_input:
            return

        task_data = {
            "gflow_path": self.parent.get_gflow_path(),
            "path": path,
            "output_options": self.output_options,
        }
        # https://gis.stackexchange.com/questions/296175/issues-with-qgstask-and-task-manager
        # It seems the task goes awry when not associated with a Python object!
        # -- we just assign it to the widget here.
        #
        # To run the tasks without the QGIS task manager:
        # result = task.run()
        # task.finished(result)

        # Remove the output layers from QGIS, otherwise they cannot be overwritten.
        gpkg_path = str(path)
        for layer in QgsProject.instance().mapLayers().values():
            if Path(gpkg_path) == Path(layer.source()):
                QgsProject.instance().removeMapLayer(layer.id())

        self.compute_task = ComputeTask(self, task_data, self.parent.message_bar)
        self.set_interpreter_interaction(False)
        QgsApplication.taskManager().addTask(self.compute_task)
        return

    def domain(self) -> None:
        """Write the current viewing extent as rectangle to the GeoPackage."""
        item = self.parent.domain_item()
        ymax, ymin = item.element.update_extent(self.parent.iface)
        self.set_spacing_from_domain(ymax, ymin)
        self.parent.iface.mapCanvas().refreshAllLayers()
        return

    def set_spacing_from_domain(self, ymax: float, ymin: float) -> None:
        # Guess a reasonable value for the spacing: about 50 rows
        dy = (ymax - ymin) / 50.0
        if dy > 500.0:
            dy = round(dy / 500.0) * 500.0
        elif dy > 50.0:
            dy = round(dy / 50.0) * 50.0
        elif dy > 5.0:  # round to five
            dy = round(dy / 5.0) * 5.0
        elif dy > 1.0:
            dy = round(dy)
        self.spacing_spin_box.setValue(dy)
        return

    def load_raster_result(self, path: Union[Path, str], contours: bool) -> None:
        # String for QGIS functions
        path = Path(path)
        raster_path = str(path.with_suffix(".grd")).upper()
        layer = QgsRasterLayer(raster_path, "head", "gdal")
        renderer, minimum, maximum = layer_styling.pseudocolor_renderer(
            layer, band=1, colormap="Plasma", nclass=10
        )
        layer.setRenderer(renderer)
        layer.setCrs(self.parent.crs)
        self.parent.output_group.add_layer(layer, "raster")

        if contours:
            # Should generally result in 20 contours.
            step = (maximum - minimum) / 21
            # If no head differences are present, no contours can be drawn.
            if step == 0.0:
                return

            contour_layer = raster_contours(
                gpkg_path=str(path.with_suffix(".output.gpkg")),
                layer=layer,
                name="head-contours",
                start=minimum,
                stop=maximum,
                step=step,
            )
            self.add_contour_layer(contour_layer)

        return

    def load_pathlines_result(self, path: Union[Path, str]) -> None:
        from PyQt5.QtCore import Qt, QVariant
        from qgis.core import (
            QgsVectorLayer,
            QgsPointXY,
            QgsFeature,
            QgsGeometry,
            QgsField,
        )
        from qgis.core.additions.edit import edit
        from gflow.core import geopackage

        path = Path(path)
        pathlines_path = str(path.with_suffix(".pth")).upper()

        with open(pathlines_path) as f:
            lines = f.readlines()

        # Split the lines per polyline
        linestrings = []
        vertices = []
        for line in lines:
            # Start and end lines are duplicated.
            if line.startswith("START"):
                # Clear the vertices
                vertices = []
            elif line.startswith("END"):
                # Store the list of vertices
                linestrings.append(vertices)
            else:
                # So far, we're only interested in x, y, z
                x, y, z = [float(v) for v in line[4:47].split()]
                vertices.append((QgsPointXY(x, y), z))

        layer = QgsVectorLayer("LineString", "Pathlines", "memory")
        provider = layer.dataProvider()
        provider.addAttributes(
            (
                QgsField("start_elevation", QVariant.Double),
                QgsField("end_elevation", QVariant.Double),
            )
        )
        layer.updateFields()
        layer.setCrs(self.parent.crs)
        fields = layer.fields()

        features = []
        for linestring in linestrings:
            for (vertex0, z0), (vertex1, z1) in zip(linestring[:-1], linestring[1:]):
                geometry = QgsGeometry.fromPolylineXY((vertex0, vertex1))
                feature = QgsFeature(fields)
                feature.setGeometry(geometry)
                feature.setAttribute("start_elevation", z0)
                feature.setAttribute("end_elevation", z1)
                features.append(feature)

        with edit(layer):
            layer.addFeatures(features)

        gpkg_path = str(path.with_suffix(".output.gpkg"))
        newfile = not Path(gpkg_path).exists()
        written_layer = geopackage.write_layer(
            path=gpkg_path,
            layer=layer,
            layername="Pathlines",
            newfile=newfile,
        )

        self.parent.output_group.add_layer(written_layer, "vector", on_top=True)
        return

    def load_extract_result(self, path: Union[Path, str]) -> None:
        path = Path(path)
        extract_path = Path(str(path.with_suffix(".xtr")).upper())
        vector_layers = extraction_to_layers(
            extract_path,
            crs=self.parent.crs,
            gpkg_path=str(path.with_suffix(".output.gpkg")),
        )
        for layer in vector_layers:
            self.parent.output_group.add_layer(layer, "vector", on_top=False)
        return
