class GflowExtractParser:
    def __init__(self, lines: list[str]):
        self.lines = lines
        self.count = 0
        self.n = len(lines)

    def peek(self) -> str:
        return self.lines[self.count]

    def advance(self) -> str:
        line = self.peek()
        self.count += 1
        return line

    def done(self) -> bool:
        return self.count >= (self.n - 1)

    @staticmethod
    def _end_of_block(line) -> bool:
        return line.startswith("*") or line.startswith("!")

    def advance_block(self, attributes) -> list[dict]:
        line = self.peek()
        records = []
        while not self._end_of_block(line):
            line = self.advance()[1:]
            record = {}
            for key, value in zip(attributes, line.split(",")):
                value = value.strip()
                if key == "label":
                    record[key] = value
                else:
                    try:
                        record[key] = float(value)
                    except ValueError:
                        record[key] = None
            records.append(record)
            line = self.peek()
        return records
