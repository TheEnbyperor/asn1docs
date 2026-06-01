import dataclasses
import typing
import markdown_it
import pyparsing

JavaDocElement = typing.Union["JavaDocText", "JavaDocTag"]
md = markdown_it.MarkdownIt()


@dataclasses.dataclass
class JavaDocText:
    TYPE = "text"
    text: str

    def render(self) -> str:
        return md.render(self.text)


@dataclasses.dataclass
class JavaDocTag:
    TYPE = "tag"
    tag: str
    text: str

    def render(self) -> str:
        return md.render(self.text)


@dataclasses.dataclass
class JavaDoc:
    segments: typing.List[JavaDocElement]

    @classmethod
    def build(cls, type_def: pyparsing.ParseResults) -> "JavaDoc":
        segments = []
        last_segment = None
        for line in type_def.lines:
            if line.text:
                if isinstance(last_segment, JavaDocText):
                    last_segment.text += "\n"
                    last_segment.text += line.text
                else:
                    if last_segment:
                        segments.append(last_segment)
                    last_segment = JavaDocText(line.text)
            elif line.tagged:
                if last_segment:
                    segments.append(last_segment)
                last_segment = JavaDocTag(
                    tag=line.tagged.tag,
                    text=line.tagged.text.strip(),
                )
            else:
                if isinstance(last_segment, JavaDocText):
                    last_segment.text += "\n"
                else:
                    if last_segment:
                        segments.append(last_segment)
                    last_segment = JavaDocText("")
        if last_segment:
            segments.append(last_segment)
        return cls(segments=segments)



