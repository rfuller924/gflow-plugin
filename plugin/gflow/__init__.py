"""This script initializes the plugin, making it known to QGIS."""


def classFactory(iface):  # pylint: disable=invalid-name
    from .gflow import GflowPlugin

    return GflowPlugin(iface)
