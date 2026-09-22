"""Idempotently add a bidirectional transparent-NTN communications model to STK."""

from __future__ import annotations

import argparse

from agi.stk12.stkdesktop import STKDesktop
from agi.stk12.stkobjects import AgESTKObjectType


def iter_children(obj):
    children = getattr(obj, "Children", None)
    if children is None:
        return
    for index in range(children.Count):
        child = children.Item(index)
        yield child
        yield from iter_children(child)


def first_object(scenario, class_name, preferred_name=None):
    objects = [obj for obj in iter_children(scenario) if str(obj.ClassName) == class_name]
    if preferred_name:
        for obj in objects:
            if str(obj.InstanceName) == preferred_name:
                return obj
    if not objects:
        raise RuntimeError(f"active scenario has no {class_name}")
    return objects[0]


def child(root, parent, object_type, class_name, name):
    path = f"{parent.Path}/{class_name}/{name}"
    try:
        return root.GetObjectFromPath(path), False
    except Exception:
        return parent.Children.New(object_type, name), True


def configure_transmitter(obj, frequency_hz, power_dbw, data_rate_bps):
    obj.SetModel("Complex Transmitter Model")
    model = obj.Model
    model.Frequency = frequency_hz
    model.Power = power_dbw
    model.DataRate = data_rate_bps
    model.AntennaControl.SetEmbeddedModel("Isotropic")


def configure_receiver(obj, frequency_hz):
    obj.SetModel("Complex Receiver Model")
    model = obj.Model
    model.AutoTrackFrequency = False
    model.Frequency = frequency_hz
    model.AutoSelectDemodulator = True
    model.AutoScaleBandwidth = True
    model.UseRain = False
    model.AntennaControl.SetEmbeddedModel("Isotropic")
    try:
        model.SystemNoiseTemperature.ConstantNoiseTemperature = 290.0
    except Exception:
        pass


def configure_chain(root, scenario, name, objects):
    chain, created = child(root, scenario, AgESTKObjectType.eChain, "Chain", name)
    try:
        chain.Objects.RemoveAll()
    except Exception:
        # Some STK 12 builds expose Clear() instead.
        try:
            chain.Objects.Clear()
        except Exception:
            if not created:
                raise RuntimeError(f"cannot clear existing chain {name}")
    for obj in objects:
        chain.Objects.AddObject(obj)
    return chain, created


def main() -> int:
    parser = argparse.ArgumentParser(description="Build OAI UL/DL transparent NTN chains in active STK scene")
    parser.add_argument("--satellite-name", default="QIANFAN-166_69383")
    parser.add_argument("--ground-name", default="Beijing")
    parser.add_argument("--ue-name", default="OAI_UE")
    parser.add_argument("--dl-frequency-hz", type=float, default=2_488_400_000.0)
    parser.add_argument("--ul-frequency-hz", type=float, default=1_614_900_000.0)
    parser.add_argument("--tx-power-dbw", type=float, default=30.0)
    parser.add_argument("--data-rate-bps", type=float, default=1_000_000.0)
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args()

    desktop = STKDesktop.AttachToApplication()
    root = desktop.Root
    scenario = root.CurrentScenario
    satellite = first_object(scenario, "Satellite", args.satellite_name)
    ground = first_object(scenario, "Place", args.ground_name)

    ue, ue_created = child(root, scenario, AgESTKObjectType.ePlace, "Place", args.ue_name)
    if ue_created:
        try:
            ue.Position.AssignPlanetodetic(*ground.Position.QueryPlanetodeticArray())
        except Exception:
            ue.Position.AssignCartesian(*ground.Position.QueryCartesianArray())

    gnb_dl_tx, _ = child(root, ground, AgESTKObjectType.eTransmitter, "Transmitter", "OAI_gNB_DL_Tx")
    gnb_ul_rx, _ = child(root, ground, AgESTKObjectType.eReceiver, "Receiver", "OAI_gNB_UL_Rx")
    ue_ul_tx, _ = child(root, ue, AgESTKObjectType.eTransmitter, "Transmitter", "OAI_UE_UL_Tx")
    ue_dl_rx, _ = child(root, ue, AgESTKObjectType.eReceiver, "Receiver", "OAI_UE_DL_Rx")
    sat_ul_rx, _ = child(root, satellite, AgESTKObjectType.eReceiver, "Receiver", "OAI_SAT_UL_Rx")
    sat_ul_tx, _ = child(root, satellite, AgESTKObjectType.eTransmitter, "Transmitter", "OAI_SAT_UL_Tx")
    sat_dl_rx, _ = child(root, satellite, AgESTKObjectType.eReceiver, "Receiver", "OAI_SAT_DL_Rx")
    sat_dl_tx, _ = child(root, satellite, AgESTKObjectType.eTransmitter, "Transmitter", "OAI_SAT_DL_Tx")

    configure_transmitter(gnb_dl_tx, args.dl_frequency_hz, args.tx_power_dbw, args.data_rate_bps)
    configure_receiver(gnb_ul_rx, args.ul_frequency_hz)
    configure_transmitter(ue_ul_tx, args.ul_frequency_hz, args.tx_power_dbw, args.data_rate_bps)
    configure_receiver(ue_dl_rx, args.dl_frequency_hz)
    configure_receiver(sat_ul_rx, args.ul_frequency_hz)
    configure_transmitter(sat_ul_tx, args.ul_frequency_hz, args.tx_power_dbw, args.data_rate_bps)
    configure_receiver(sat_dl_rx, args.dl_frequency_hz)
    configure_transmitter(sat_dl_tx, args.dl_frequency_hz, args.tx_power_dbw, args.data_rate_bps)

    ul_chain, _ = configure_chain(root, scenario, "OAI_UL", (ue_ul_tx, sat_ul_rx, sat_ul_tx, gnb_ul_rx))
    dl_chain, _ = configure_chain(root, scenario, "OAI_DL", (gnb_dl_tx, sat_dl_rx, sat_dl_tx, ue_dl_rx))

    if args.save:
        save = getattr(root, "SaveScenario", None)
        if callable(save):
            save()
        else:
            raise RuntimeError("this STK API does not expose SaveScenario; save the scenario in the STK window")

    print(f"Scenario: {scenario.InstanceName}")
    print(f"Satellite: {satellite.Path}")
    print(f"gNB ground site: {ground.Path}")
    print(f"UE ground site: {ue.Path}")
    print(f"UL chain: {ul_chain.Path}")
    print(f"DL chain: {dl_chain.Path}")
    print(f"UL frequency: {args.ul_frequency_hz:.3f} Hz")
    print(f"DL frequency: {args.dl_frequency_hz:.3f} Hz")
    print("Antenna model: Isotropic; modulation: BPSK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
