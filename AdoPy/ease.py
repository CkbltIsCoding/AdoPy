from math import pi, sin, cos, sqrt

c1 = 1.70158
c2 = c1 * 1.525
c3 = c1 + 1
c4 = (2 * pi) / 3
c5 = (2 * pi) / 4.5
n1 = 7.5625
d1 = 2.75


def out_bounce(x):
    if x < 1 / d1:
        return n1 * x * x
    elif x < 2 / d1:
        x -= 1.5
        return n1 * (x / d1) * x + 0.75
    elif x < 2.5 / d1:
        x -= 2.25
        return n1 * (x / d1) * x + 0.9375
    else:
        x -= 2.625
        return n1 * (x / d1) * x + 0.984375


def ease(_ease, x):
    if x <= 0:
        return 0
    elif x >= 1:
        return 1
    match _ease:
        case "Linear":
            return x
        case "InSine":
            return 1 - cos((x * pi) / 2)
        case "OutSine":
            return sin((x * pi) / 2)
        case "InOutSine":
            return -(cos(pi * x) - 1) / 2
        case "InQuad":
            return x * x
        case "OutQuad":
            return 1 - (1 - x) * (1 - x)
        case "InOutQuad":
            return 2 * x * x if x < 0.5 else 1 - pow(-2 * x + 2, 2) / 2
        case "InCubic":
            return x * x * x
        case "OutCubic":
            return 1 - pow(1 - x, 3)
        case "InOutCubic":
            return 4 * x * x * x if x < 0.5 else 1 - pow(-2 * x + 2, 3) / 2
        case "InQuart":
            return x * x * x * x
        case "OutQuart":
            return 1 - pow(1 - x, 4)
        case "InOutQuart":
            return 8 * x * x * x * x if x < 0.5 else 1 - pow(-2 * x + 2, 4) / 2
        case "InQuint":
            return x * x * x * x * x
        case "OutQuint":
            return 1 - pow(1 - x, 5)
        case "InOutQuint":
            return 16 * x * x * x * x * x if x < 0.5 else 1 - pow(-2 * x + 2, 5) / 2
        case "InExpo":
            return 0 if x == 0 else pow(2, 10 * x - 10)
        case "OutExpo":
            return 1 if x == 1 else 1 - pow(2, -10 * x)
        case "InOutExpo":
            if x == 0 or x == 1:
                return x
            return pow(2, 20 * x - 10) / 2 if x < 0.5 else (2 - pow(2, -20 * x + 10)) / 2
        case "InCirc":
            return 1 - sqrt(1 - pow(x, 2))
        case "OutCirc":
            return sqrt(1 - pow(x - 1, 2))
        case "InOutCirc":
            return ((1 - sqrt(1 - pow(2 * x, 2))) / 2
                    if x < 0.5 else
                    (sqrt(1 - pow(-2 * x + 2, 2)) + 1) / 2)
        case "InBack":
            return c3 * x * x * x - c1 * x * x
        case "OutBack":
            return 1 + c3 * pow(x - 1, 3) + c1 * pow(x - 1, 2)
        case "InOutBack":
            return ((pow(2 * x, 2) * ((c2 + 1) * 2 * x - c2)) / 2
                    if x < 0.5 else
                    (pow(2 * x - 2, 2) * ((c2 + 1) * (x * 2 - 2) + c2) + 2) / 2)
        case "InElastic":
            return x if x == 0 or x == 1 else -pow(2, 10 * x - 10) * sin((x * 10 - 10.75) * c4)
        case "OutElastic":
            return x if x == 0 or x == 1 else pow(2, -10 * x) * sin((x * 10 - 0.75) * c4) + 1
        case "InOutElastic":
            if x == 0 or x == 1:
                return x
            return (-(pow(2, 20 * x - 10) * sin((20 * x - 11.125) * c5)) / 2
                    if x < 0.5 else
                    (pow(2, -20 * x + 10) * sin((20 * x - 11.125) * c5)) / 2 + 1)
        case "InBounce":
            return 1 - out_bounce(1 - x)
        case "OutBounce":
            return out_bounce(x)
        case "InOutBounce":
            return ((1 - out_bounce(1 - 2 * x)) / 2
                    if x < 0.5 else
                    (1 + out_bounce(2 * x - 1)) / 2)
        case _:
            raise NameError(_ease)
