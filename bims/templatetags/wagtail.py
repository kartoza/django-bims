import re
import wagtail.admin.rich_text.editors.draftail.features as draftail_features
from wagtail.core import hooks
from wagtail.admin.rich_text.converters import html_to_contentstate
from wagtail.admin.rich_text.converters.html_to_contentstate import (
    BlockElementHandler, KEEP_WHITESPACE, WHITESPACE_RE
)
# Regex that matches nothing
NOTHING_RE = re.compile('a^')


class PreformattedTextElementHandler(BlockElementHandler):
    """
    BlockElementHandler that preserves all whitespace.
    """
    def handle_starttag(self, name, attrs, state, contentstate):
        # Keep all whitespace while rendering this block
        html_to_contentstate.WHITESPACE_RE = NOTHING_RE
        state.leading_whitespace = KEEP_WHITESPACE
        super(
            PreformattedTextElementHandler, self
        ).handle_starttag(name, attrs, state, contentstate)

    def handle_endtag(self, name, state, contentstate):
        # Reset whitespace handling to normal behaviour
        html_to_contentstate.WHITESPACE_RE = WHITESPACE_RE
        super(
            PreformattedTextElementHandler, self
        ).handle_endtag(name, state, contentstate)


@hooks.register('register_rich_text_features')
def register_code_block_feature(features):
    """
    Register the `code-block` feature, which uses the
    `code-block` Draft.js block type and store it as
    HTML within a `<pre class="code">` tag.
    """
    feature_name = 'code-block'
    feature_type = 'code-block'

    control = {
        'type': feature_type,
        'label': '{}',
        'description': 'Code',
    }

    features.register_editor_plugin(
        'draftail', feature_name, draftail_features.BlockFeature(control)
    )

    features.register_converter_rule('contentstate', feature_name, {
        'from_database_format': {
            'pre': PreformattedTextElementHandler(feature_type),
        },
        'to_database_format': {
            'block_map': {
                feature_type: {
                    'element': 'pre',
                    'props': {'class': 'code'},
                },
            },
        },
    })

    features.default_features.append(feature_name)
    features.default_features.append('code')
    features.default_features.append('blockquote')
