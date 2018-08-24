from haystack.utils import Highlighter
from django.utils.html import strip_tags


class CustomHighlighter(Highlighter):
    def highlight(self, text_block):
        self.text_block = strip_tags(text_block)
        highlight_locations = self.find_highlightable_words()
        start_offset = 0
        end_offset = len(self.text_block)
        return self.render_html(highlight_locations,
                                start_offset,
                                end_offset)
