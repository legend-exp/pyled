import leds


def test_core():
    assert leds.greet() == 'Hello leds!'
