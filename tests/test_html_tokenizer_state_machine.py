import pytest

from gorushi.state_machine import HTMLTokenizerStateMachine, HTMLTokenizerState


@pytest.mark.ci
def test_html_tokenizer_state_machine_with_basic_form():
    state_machine = HTMLTokenizerStateMachine()
    state_machine.process_string("<html><!-- Comment --><body></body></html>")
    assert state_machine.state == HTMLTokenizerState.TEXT


@pytest.mark.ci
def test_comment_tag_handling():
    state_machine = HTMLTokenizerStateMachine()
    state_machine.process_string("<!-- This is a comment -->") 
    _ = state_machine.flush_buffer()
    state_machine.process_string("-->")
    assert state_machine.state == HTMLTokenizerState.TEXT
    assert "".join(state_machine.buffer).strip() == '-->'

    state_machine = HTMLTokenizerStateMachine()
    state_machine.process_string("Some text <!-- Comment starts")
    assert state_machine.state == HTMLTokenizerState.COMMENT


@pytest.mark.ci
def test_self_closed_comment():
    state_machine = HTMLTokenizerStateMachine()
    state_machine.process_string("<!--->")
    assert state_machine.state == HTMLTokenizerState.TEXT


@pytest.mark.ci
def test_nested_comments():
    state_machine = HTMLTokenizerStateMachine()
    state_machine.process_string("<!-- Comment <!-- Nested -->") 
    buffered_content = state_machine.flush_buffer()
    state_machine.process_string("Still in comment -->")
    assert state_machine.state == HTMLTokenizerState.TEXT
    buffered_content = state_machine.flush_buffer()
    assert "".join(buffered_content).strip() == "Still in comment -->"


@pytest.mark.ci
def test_script_tag_handling():
    state_machine = HTMLTokenizerStateMachine()
    state_machine.process_string("<script><!-- var a = 1; -->")
    assert state_machine.state == HTMLTokenizerState.SCRIPT_DATA
    buffered_content = state_machine.flush_buffer()
    assert "".join(buffered_content) == '<!-- var a = 1; -->'


@pytest.mark.ci
def test_comment_handling_within_script():
    state_machine = HTMLTokenizerStateMachine()
    state_machine.process_string("<script><!-- This is a comment -->")
    assert state_machine.state == HTMLTokenizerState.SCRIPT_DATA
    buffered_content = state_machine.flush_buffer()
    assert "".join(buffered_content) == '<!-- This is a comment -->'


@pytest.mark.ci
def test_closing_script_tag():
    state_machine = HTMLTokenizerStateMachine()
    state_machine.process_string("<script>var a = 1;</script>")
    assert state_machine.state == HTMLTokenizerState.TEXT
    buffered_content = state_machine.flush_buffer()
    assert "".join(buffered_content) == 'var a = 1;'


@pytest.mark.ci
def test_script_tag_with_nested_contents():
    state_machine = HTMLTokenizerStateMachine()
    state_machine.process_string("<script>if (a < b) { console.log('Hello'); }</script>")
    assert state_machine.state == HTMLTokenizerState.TEXT
    buffered_content = state_machine.flush_buffer()
    assert "".join(buffered_content) == "if (a < b) { console.log('Hello'); }"


@pytest.mark.ci 
def test_tag_attributes_handling():
    state_machine = HTMLTokenizerStateMachine()
    result = state_machine.process_string("<div class='container' id=\"main\">")
    assert state_machine.state == HTMLTokenizerState.TEXT
    assert "".join(result) == "div class='container' id=\"main\""


@pytest.mark.ci 
def test_incomplete_tag_attribute_handling():
    state_machine = HTMLTokenizerStateMachine()
    state_machine.process_string("<div class='contai")
    assert state_machine.state == HTMLTokenizerState.ATTRIBUTE_OPEN

    state_machine.process_string("ner' id=\"main\">")
    assert state_machine.state == HTMLTokenizerState.TEXT


@pytest.mark.ci 
def test_tailwind_style_class_parsing():
    state_machine = HTMLTokenizerStateMachine()
    result = state_machine.process_string("<div class=\"bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded\">")
    assert state_machine.state == HTMLTokenizerState.TEXT
    assert "".join(result) == "div class=\"bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded\""

