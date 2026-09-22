"""Inspect the active STK scenario for communications objects and link providers."""

from agi.stk12.stkdesktop import STKDesktop


COMM_CLASSES = {"Transmitter", "Receiver", "Chain", "CommSystem", "Antenna"}


def iter_children(obj):
    children = getattr(obj, "Children", None)
    if children is None:
        return
    for index in range(children.Count):
        child = children.Item(index)
        yield child
        yield from iter_children(child)


def provider_names(obj):
    providers = getattr(obj, "DataProviders", None)
    if providers is None:
        return []
    names = []
    for index in range(providers.Count):
        provider = providers.Item(index)
        names.append(str(provider.Name))
    return names


def describe_provider(collection, name):
    try:
        provider = collection.Item(name)
    except Exception as exc:
        return f"unavailable ({exc})"
    try:
        elements = provider.Elements
        return ", ".join(str(elements.Item(i).Name) for i in range(elements.Count))
    except Exception:
        pass
    try:
        group = provider.Group
        return "groups: " + ", ".join(str(group.Item(i).Name) for i in range(group.Count))
    except Exception as exc:
        return f"cannot enumerate ({exc})"


def main():
    desktop = STKDesktop.AttachToApplication()
    root = desktop.Root
    scenario = root.CurrentScenario
    print(f"Scenario: {scenario.InstanceName}")
    print(f"CurrentTime: {root.CurrentTime}")
    print("Objects:")

    comm_objects = []
    for obj in iter_children(scenario):
        class_name = str(obj.ClassName)
        path = str(obj.Path)
        print(f"  {class_name}: {path}")
        if class_name in COMM_CLASSES:
            comm_objects.append(obj)

    print("\nCommunications objects:")
    if not comm_objects:
        print("  NONE")
        print("  A Transmitter/Receiver/Chain must be created for STK link-budget metrics.")
        return

    for obj in comm_objects:
        print(f"  {obj.ClassName}: {obj.Path}")
        names = provider_names(obj)
        matching = [name for name in names if "Link" in name or "AER" in name]
        if matching:
            print("    Providers: " + ", ".join(matching))
        if str(obj.ClassName) == "Chain":
            print("    Link Information elements: " + describe_provider(obj.DataProviders, "Link Information"))

    transmitters = [obj for obj in comm_objects if str(obj.ClassName) == "Transmitter"]
    receivers = [obj for obj in comm_objects if str(obj.ClassName) == "Receiver"]
    for transmitter in transmitters:
        for receiver in receivers:
            try:
                access = transmitter.GetAccessToObject(receiver)
            except Exception:
                continue
            print(f"\nLink {transmitter.Path} -> {receiver.Path}:")
            for provider_name in ("AER Data", "Link Information"):
                print(f"  {provider_name}: {describe_provider(access.DataProviders, provider_name)}")


if __name__ == "__main__":
    main()
