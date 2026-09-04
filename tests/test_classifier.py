import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))

from app.services.classifier import (
    classify_intent,
    TOOL_RETRIEVE_AND_ANSWER,
    TOOL_WRITE_SHIP30_ESSAY,
    TOOL_GENERATE_ARTIFACT
)

def test_classify_ship30_essay():
    prompt1 = "Write a Ship 30/30 essay on Founder Mode based on Brian Chesky's transcript."
    prompt2 = "Generate an atomic essay analyzing Elena Verna PLG insights."
    assert classify_intent(prompt1) == TOOL_WRITE_SHIP30_ESSAY
    assert classify_intent(prompt2) == TOOL_WRITE_SHIP30_ESSAY

def test_classify_generate_artifact():
    prompt1 = "Create an HTML visual table component comparing Empowered Teams vs Feature Factories."
    prompt2 = "Render an HTML dashboard card summarizing the SPADE framework."
    assert classify_intent(prompt1) == TOOL_GENERATE_ARTIFACT
    assert classify_intent(prompt2) == TOOL_GENERATE_ARTIFACT

def test_classify_retrieve_and_answer():
    prompt1 = "What is Product-Led Growth according to Elena Verna?"
    prompt2 = "Explain how Shreyas Doshi defines Product Sense."
    assert classify_intent(prompt1) == TOOL_RETRIEVE_AND_ANSWER
    assert classify_intent(prompt2) == TOOL_RETRIEVE_AND_ANSWER
