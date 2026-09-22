"""Dump public properties of communications objects in the active STK scenario."""

from agi.stk12.stkdesktop import STKDesktop


def iter_children(obj):
    children = getattr(obj, "Children", None)
    if children is None:
        return
    for index in range(children.Count):
        child = children.Item(index)
        yield child
        yield from iter_children(child)


def dump_properties(label, obj):
    print(f"\n{label}: {type(obj).__name__}")
    for name in sorted(item for item in dir(obj) if not item.startswith("_")):
        if name.startswith(("Get", "Set", "Query", "Compute")):
            continue
        try:
            value = getattr(obj, name)
        except Exception:
            continue
        if callable(value):
            continue
        if isinstance(value, (str, int, float, bool)):
            print(f"  {name} = {value!r}")


desktop = STKDesktop.AttachToApplication()
root = desktop.Root
scenario = root.CurrentScenario
for obj in iter_children(scenario):
    if str(obj.ClassName) not in ("Transmitter", "Receiver"):
        continue
    print(f"\nOBJECT {obj.Path}")
    print("  API members containing model:", [name for name in dir(obj) if "model" in name.lower()])
    dump_properties("object", obj)
    try:
        model = obj.Model
        dump_properties("model", model)
        for member in dir(model):
            if any(token in member.lower() for token in ("antenna", "modulat", "demod", "systemnoise")):
                try:
                    nested = getattr(model, member)
                except Exception:
                    continue
                if not callable(nested):
                    dump_properties(f"model.{member}", nested)
                    if member == "AntennaControl":
                        print(
                            "  AntennaControl API members:",
                            [name for name in dir(nested) if not name.startswith("_")],
                        )
                        try:
                            print("  Supported embedded models:", list(nested.SupportedEmbeddedModels))
                        except Exception:
                            pass
                        for antenna_member in ("EmbeddedModel", "AntennaModel"):
                            try:
                                dump_properties(
                                    f"model.AntennaControl.{antenna_member}",
                                    getattr(nested, antenna_member),
                                )
                            except Exception:
                                pass
    except Exception as exc:
        print(f"  model unavailable: {exc}")
