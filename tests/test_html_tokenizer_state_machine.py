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


