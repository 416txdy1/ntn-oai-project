stk.v.12.0
WrittenBy    STK_v12.2.0

BEGIN Transmitter

    Name		 OAI_SAT_DL_Tx
<?xml version = "1.0" standalone = "yes"?>
<SCOPE>
    <VAR name = "Model">
        <SCOPE Class = "LinkEmbedControl">
            <VAR name = "ReferenceType">
                <STRING>&quot;Unlinked&quot;</STRING>
            </VAR>
            <VAR name = "Component">
                <VAR name = "Complex_Transmitter_Model">
                    <SCOPE Class = "Transmitter">
                        <VAR name = "Version">
                            <STRING>&quot;1.0.1 a&quot;</STRING>
                        </VAR>
                        <VAR name = "IdentifierInformation">
                            <SCOPE>
                                <VAR name = "Identifier">
                                    <STRING>&quot;{CC3DE3DA-0A92-461A-8AAD-406520F9A1A0}&quot;</STRING>
                                </VAR>
                                <VAR name = "Version">
                                    <STRING>&quot;39&quot;</STRING>
                                </VAR>
                                <VAR name = "SourceIdentifierInformation">
                                    <SCOPE>
                                        <VAR name = "Identifier">
                                            <STRING>&quot;{D405DF60-857E-4AF9-BE4A-21AB56A790FC}&quot;</STRING>
                                        </VAR>
                                        <VAR name = "Version">
                                            <STRING>&quot;1&quot;</STRING>
                                        </VAR>
                                    </SCOPE>
                                </VAR>
                            </SCOPE>
                        </VAR>
                        <VAR name = "ComponentName">
                            <STRING>&quot;Complex_Transmitter_Model&quot;</STRING>
                        </VAR>
                        <VAR name = "Description">
                            <STRING>&quot;Complex model of a transmitter&quot;</STRING>
                        </VAR>
                        <VAR name = "Type">
                            <STRING>&quot;Complex Transmitter Model&quot;</STRING>
                        </VAR>
                        <VAR name = "UserComment">
                            <STRING>&quot;Complex model of a transmitter&quot;</STRING>
                        </VAR>
                        <VAR name = "ReadOnly">
                            <BOOL>false</BOOL>
                        </VAR>
                        <VAR name = "Clonable">
                            <BOOL>true</BOOL>
                        </VAR>
                        <VAR name = "Category">
                            <STRING>&quot;@Top&quot;</STRING>
                        </VAR>
                        <VAR name = "UseFilter">
                            <BOOL>false</BOOL>
                        </VAR>
                        <VAR name = "Filter">
                            <SCOPE Class = "LinkEmbedControl">
                                <VAR name = "ReferenceType">
                                    <STRING>&quot;Unlinked&quot;</STRING>
                                </VAR>
                                <VAR name = "Component">
                                    <VAR name = "Butterworth">
                                        <SCOPE Class = "Filter">
                                            <VAR name = "Version">
                                                <STRING>&quot;1.0.0 a&quot;</STRING>
                                            </VAR>
                                            <VAR name = "IdentifierInformation">
                                                <SCOPE>
                                                    <VAR name = "Identifier">
                                                        <STRING>&quot;{CC3776EF-7C63-46CE-89EA-940E8C4AC2D1}&quot;</STRING>
                                                    </VAR>
                                                    <VAR name = "Version">
                                                        <STRING>&quot;1&quot;</STRING>
                                                    </VAR>
                                                    <VAR name = "SourceIdentifierInformation">
                                                        <SCOPE>
                                                            <VAR name = "Identifier">
                                                                <STRING>&quot;{7ADF0949-E1C7-4B01-A96F-9F197950D5BB}&quot;</STRING>
                                                            </VAR>
                                                            <VAR name = "Version">
                                                                <STRING>&quot;1&quot;</STRING>
                                                            </VAR>
                                                        </SCOPE>
                                                    </VAR>
                                                </SCOPE>
                                            </VAR>
                                            <VAR name = "ComponentName">
                                                <STRING>&quot;Butterworth&quot;</STRING>
                                            </VAR>
                                            <VAR name = "Description">
                                                <STRING>&quot;General form of nth order Butterworth filter with flat passband and stopband regions&quot;</STRING>
                                            </VAR>
                                            <VAR name = "Type">
                                                <STRING>&quot;Butterworth&quot;</STRING>
                                            </VAR>
                                            <VAR name = "UserComment">
                                                <STRING>&quot;General form of nth order Butterworth filter with flat passband and stopband regions&quot;</STRING>
                                            </VAR>
                                            <VAR name = "ReadOnly">
                                                <BOOL>false</BOOL>
                                            </VAR>
                                            <VAR name = "Clonable">
                                                <BOOL>true</BOOL>
                                            </VAR>
                                            <VAR name = "Category">
                                                <STRING>&quot;@Top&quot;</STRING>
                                            </VAR>
                                            <VAR name = "LowerBandwidthLimit">
                                                <QUANTITY Dimension = "BandwidthUnit" Unit = "Hz">
                                                    <REAL>-20000000</REAL>
                                                </QUANTITY>
                                            </VAR>
                                            <VAR name = "UpperBandwidthLimit">
                                                <QUANTITY Dimension = "BandwidthUnit" Unit = "Hz">
                                                    <REAL>20000000</REAL>
                                                </QUANTITY>
                                            </VAR>
                                            <VAR name = "InsertionLoss">
                                                <QUANTITY Dimension = "RatioUnit" Unit = "units">
                                                    <REAL>1</REAL>
                                                </QUANTITY>
                                            </VAR>
                                            <VAR name = "Order">
                                                <INT>4</INT>
                                            </VAR>
                                            <VAR name = "CutoffFrequency">
                                                <QUANTITY Dimension = "BandwidthUnit" Unit = "Hz">
                                                    <REAL>10000000</REAL>
                                                </QUANTITY>
                                            </VAR>
                                        </SCOPE>
                                    </VAR>
                                </VAR>
                            </SCOPE>
                        </VAR>
                        <VAR name = "PostTransmitGainsLosses">
                            <SCOPE>
                                <VAR name = "GainLossList">
                                    <LIST />
                                </VAR>
                            </SCOPE>
                        </VAR>
                        <VAR name = "Frequency">
                            <QUANTITY Dimension = "FrequencyUnit" Unit = "Hz">
                                <REAL>2488400000</REAL>
                            </QUANTITY>
                        </VAR>
                        <VAR name = "Modulator">
                            <VAR name = "QPSK">
                                <SCOPE Class = "Modulator">
                                    <VAR name = "ComponentName">
                                        <STRING>&quot;QPSK&quot;</STRING>
                                    </VAR>
                                    <VAR name = "UseSignalPSD">
                                        <BOOL>false</BOOL>
                                    </VAR>
                                    <VAR name = "NumPSDNulls">
                                        <INT>15</INT>
                                    </VAR>
                                    <VAR name = "UseCDMASpread">
                                        <BOOL>false</BOOL>
                                    </VAR>
                                    <VAR name = "ChipsPerBit">
                                        <INT>1</INT>
                                    </VAR>
                                    <VAR name = "AutoScaleBandwidth">
                                        <BOOL>true</BOOL>
                                    </VAR>
                                    <VAR name = "SymmetricBandwidth">
                                        <BOOL>true</BOOL>
                                    </VAR>
                                    <VAR name = "UpperBandwidthLimit">
                                        <QUANTITY Dimension = "BandwidthUnit" Unit = "Hz">
                                            <REAL>500000</REAL>
                                        </QUANTITY>
                                    </VAR>
                                    <VAR name = "LowerBandwidthLimit">
                                        <QUANTITY Dimension = "BandwidthUnit" Unit = "Hz">
                                            <REAL>-500000</REAL>
                                        </QUANTITY>
                                    </VAR>
                                    <VAR name = "Bandwidth">
                                        <QUANTITY Dimension = "BandwidthUnit" Unit = "Hz">
                                            <REAL>1000000</REAL>
                                        </QUANTITY>
                                    </VAR>
                                    <VAR name = "Type">
                                        <STRING>&quot;QPSK&quot;</STRING>
                                    </VAR>
                                </SCOPE>
                            </VAR>
                        </VAR>
                        <VAR name = "DataRate">
                            <QUANTITY Dimension = "DataRate" Unit = "b*sec^-1">
                                <REAL>1000000</REAL>
                            </QUANTITY>
                        </VAR>
                        <VAR name = "Power">
                            <QUANTITY Dimension = "PowerUnit" Unit = "W">
                                <REAL>100</REAL>
                            </QUANTITY>
                        </VAR>
                        <VAR name = "AntennaControl">
                            <SCOPE>
                                <VAR name = "AntennaReferenceType">
                                    <STRING>&quot;Embed&quot;</STRING>
                                </VAR>
                                <VAR name = "Antenna">
                                    <SCOPE Class = "LinkEmbedControl">
                                        <VAR name = "ReferenceType">
                                            <STRING>&quot;Unlinked&quot;</STRING>
                                        </VAR>
                                        <VAR name = "Component">
                                            <VAR name = "Phased_Array">
                                                <SCOPE Class = "Antenna">
                                                    <VAR name = "Version">
                                                        <STRING>&quot;1.0.0 a&quot;</STRING>
                                                    </VAR>
                                                    <VAR name = "IdentifierInformation">
                                                        <SCOPE>
                                                            <VAR name = "Identifier">
                                                                <STRING>&quot;{51390187-5999-46C3-AD33-9D65570774F5}&quot;</STRING>
                                                            </VAR>
                                                            <VAR name = "Version">
                                                                <STRING>&quot;23&quot;</STRING>
                                                            </VAR>
                                                            <VAR name = "SourceIdentifierInformation">
                                                                <SCOPE>
                                                                    <VAR name = "Identifier">
                                                                        <STRING>&quot;{ACF1E69D-06E0-49B9-8421-8F34FE20B4AA}&quot;</STRING>
                                                                    </VAR>
                                                                    <VAR name = "Version">
                                                                        <STRING>&quot;1&quot;</STRING>
                                                                    </VAR>
                                                                </SCOPE>
                                                            </VAR>
                                                        </SCOPE>
                                                    </VAR>
                                                    <VAR name = "ComponentName">
                                                        <STRING>&quot;Phased_Array&quot;</STRING>
                                                    </VAR>
                                                    <VAR name = "Description">
                                                        <STRING>&quot;Models a phased array antenna&quot;</STRING>
                                                    </VAR>
                                                    <VAR name = "Type">
                                                        <STRING>&quot;Phased Array&quot;</STRING>
                                                    </VAR>
                                                    <VAR name = "UserComment">
                                                        <STRING>&quot;OAI engineering reference: half-wave array, target steering, +/-60 deg limits; not actual spacecraft hardware.&quot;</STRING>
                                                    </VAR>
                                                    <VAR name = "ReadOnly">
                                                        <BOOL>false</BOOL>
                                                    </VAR>
                                                    <VAR name = "Clonable">
                                                        <BOOL>true</BOOL>
                                                    </VAR>
                                                    <VAR name = "Category">
                                                        <STRING>&quot;@Top&quot;</STRING>
                                                    </VAR>
                                                    <VAR name = "DesignFrequency">
                                                        <QUANTITY Dimension = "FrequencyUnit" Unit = "Hz">
                                                            <REAL>2488400000</REAL>
                                                        </QUANTITY>
                                                    </VAR>
                                                    <VAR name = "BeamDirectionProvider">
                                                        <VAR name = "Object">
                                                            <SCOPE Class = "Direction Provider">
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                                <VAR name = "Directions">
                                                                    <LISTLINKTOOBJ>
                                                                        <STRING>&quot;Place/OAI_UE&quot;</STRING>
                                                                    </LISTLINKTOOBJ>
                                                                </VAR>
                                                                <VAR name = "AzimuthSteeringLimitA">
                                                                    <QUANTITY Dimension = "AngleUnit" Unit = "rad">
                                                                        <REAL>-1.047197551196598</REAL>
                                                                    </QUANTITY>
                                                                </VAR>
                                                                <VAR name = "AzimuthSteeringLimitB">
                                                                    <QUANTITY Dimension = "AngleUnit" Unit = "rad">
                                                                        <REAL>1.047197551196598</REAL>
                                                                    </QUANTITY>
                                                                </VAR>
                                                                <VAR name = "ElevationSteeringLimitA">
                                                                    <QUANTITY Dimension = "AngleUnit" Unit = "rad">
                                                                        <REAL>-1.047197551196598</REAL>
                                                                    </QUANTITY>
                                                                </VAR>
                                                                <VAR name = "ElevationSteeringLimitB">
                                                                    <QUANTITY Dimension = "AngleUnit" Unit = "rad">
                                                                        <REAL>1.047197551196598</REAL>
                                                                    </QUANTITY>
                                                                </VAR>
                                                                <VAR name = "LimitsExceededBehaviorType">
                                                                    <STRING>&quot;Ignore Object&quot;</STRING>
                                                                </VAR>
                                                                <VAR name = "UseDefaultDirection">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                                <VAR name = "Type">
                                                                    <STRING>&quot;Object&quot;</STRING>
                                                                </VAR>
                                                                <VAR name = "ComponentName">
                                                                    <STRING>&quot;Object&quot;</STRING>
                                                                </VAR>
                                                            </SCOPE>
                                                        </VAR>
                                                    </VAR>
                                                    <VAR name = "NullDirectionProvider">
                                                        <VAR name = "Object">
                                                            <SCOPE Class = "Direction Provider">
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                                <VAR name = "Directions">
                                                                    <LISTLINKTOOBJ />
                                                                </VAR>
                                                                <VAR name = "AzimuthSteeringLimitA">
                                                                    <QUANTITY Dimension = "AngleUnit" Unit = "rad">
                                                                        <REAL>-1.570796326794897</REAL>
                                                                    </QUANTITY>
                                                                </VAR>
                                                                <VAR name = "AzimuthSteeringLimitB">
                                                                    <QUANTITY Dimension = "AngleUnit" Unit = "rad">
                                                                        <REAL>1.570796326794897</REAL>
                                                                    </QUANTITY>
                                                                </VAR>
                                                                <VAR name = "ElevationSteeringLimitA">
                                                                    <QUANTITY Dimension = "AngleUnit" Unit = "rad">
                                                                        <REAL>-1.570796326794897</REAL>
                                                                    </QUANTITY>
                                                                </VAR>
                                                                <VAR name = "ElevationSteeringLimitB">
                                                                    <QUANTITY Dimension = "AngleUnit" Unit = "rad">
                                                                        <REAL>1.570796326794897</REAL>
                                                                    </QUANTITY>
                                                                </VAR>
                                                                <VAR name = "LimitsExceededBehaviorType">
                                                                    <STRING>&quot;Clamp-To-Limit&quot;</STRING>
                                                                </VAR>
                                                                <VAR name = "UseDefaultDirection">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                                <VAR name = "Type">
                                                                    <STRING>&quot;Object&quot;</STRING>
                                                                </VAR>
                                                                <VAR name = "ComponentName">
                                                                    <STRING>&quot;Object&quot;</STRING>
                                                                </VAR>
                                                            </SCOPE>
                                                        </VAR>
                                                    </VAR>
                                                    <VAR name = "BacklobeSuppressionType">
                                                        <STRING>&quot;Constant&quot;</STRING>
                                                    </VAR>
                                                    <VAR name = "BacklobeSuppression">
                                                        <QUANTITY Dimension = "RatioUnit" Unit = "units">
                                                            <REAL>1000</REAL>
                                                        </QUANTITY>
                                                    </VAR>
                                                    <VAR name = "IncludeElementFactor">
                                                        <BOOL>true</BOOL>
                                                    </VAR>
                                                    <VAR name = "ElementFactorExponent">
                                                        <REAL>1</REAL>
                                                    </VAR>
                                                    <VAR name = "Elements">
                                                        <LIST>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>0</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>1</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>2</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>3</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>4</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>5</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>6</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>7</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>8</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>9</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>10</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>11</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>12</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>13</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>14</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>15</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>16</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>17</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>18</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>19</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>20</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>21</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>22</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>23</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>24</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>25</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>26</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>27</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>28</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>29</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>30</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>31</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>32</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>33</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>34</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>35</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>36</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>37</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>38</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>39</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>40</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>41</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>42</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>43</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>44</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>45</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>46</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>47</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>48</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>49</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>50</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>51</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>52</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>53</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>54</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>55</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>56</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>57</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>58</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>59</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>60</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>61</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>62</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>63</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>64</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>65</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>66</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>67</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>68</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>69</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>70</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>71</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>72</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>73</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>74</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>75</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>76</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>77</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>78</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>79</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>80</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>81</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>82</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>83</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>84</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>85</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>86</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>87</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>88</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>89</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>90</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>91</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>92</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>93</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>94</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>95</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>96</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>97</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>98</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>99</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>100</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>101</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>102</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>103</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>104</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>105</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>106</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>107</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>108</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>109</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>110</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>111</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>112</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>113</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>114</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>115</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>116</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>117</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>118</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>119</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>120</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>121</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>122</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>123</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>124</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>125</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>126</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>127</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>128</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>129</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>130</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>131</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>132</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>133</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>134</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>135</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>136</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>137</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>138</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>139</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>140</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>141</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>142</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>143</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>144</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>145</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>146</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>147</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>148</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>149</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>150</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>151</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>152</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>153</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>154</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>155</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>156</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>157</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>158</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>159</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>160</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>161</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>162</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>163</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>164</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>165</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>166</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>167</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>168</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>169</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>170</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>171</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>172</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>173</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>174</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>175</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>176</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>177</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>178</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>179</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>180</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>181</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>182</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>183</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>184</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>185</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>186</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>187</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>188</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>189</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>190</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>191</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>192</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>193</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>194</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>195</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>196</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>197</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>198</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>199</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>200</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>201</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>202</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>203</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>204</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>205</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>206</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>207</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>208</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>209</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>210</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>211</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>212</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>213</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>214</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>215</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>216</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>217</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>218</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>219</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>220</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>221</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>222</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>223</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>224</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>225</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>226</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>227</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>228</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>229</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>230</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>231</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>232</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>233</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>234</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>235</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>236</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>237</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>238</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>239</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>240</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>241</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>242</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>243</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>244</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>245</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>246</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>247</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>248</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>249</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>250</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>251</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>252</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>253</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>254</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>255</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>256</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>257</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>258</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>259</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>260</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>261</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>262</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>263</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>264</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>265</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>266</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>267</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>268</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>269</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>270</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>271</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>272</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>273</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>274</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>275</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>276</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>277</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>278</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>279</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>280</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>281</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>282</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>283</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>284</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>285</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>286</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>287</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>288</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>289</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>290</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>291</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>292</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>293</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>294</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>295</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>296</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>297</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>298</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>299</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>300</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>301</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>302</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>303</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>304</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>305</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>306</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>307</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>308</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>309</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>310</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>311</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>312</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>313</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>-0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>314</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>315</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>0.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>316</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>317</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>1.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>318</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>319</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>2.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>320</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>321</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>3.75</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>322</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                            <SCOPE>
                                                                <VAR name = "X">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Y">
                                                                    <REAL>4.25</REAL>
                                                                </VAR>
                                                                <VAR name = "Id">
                                                                    <INT>323</INT>
                                                                </VAR>
                                                                <VAR name = "Enabled">
                                                                    <BOOL>false</BOOL>
                                                                </VAR>
                                                            </SCOPE>
                                                        </LIST>
                                                    </VAR>
                                                    <VAR name = "ElementConfigDesigner">
                                                        <VAR name = "Polygon">
                                                            <SCOPE Class = "ElementConfigDesigner">
                                                                <VAR name = "Type">
                                                                    <STRING>&quot;Polygon&quot;</STRING>
                                                                </VAR>
                                                                <VAR name = "Frequency">
                                                                    <QUANTITY Dimension = "FrequencyUnit" Unit = "Hz">
                                                                        <REAL>2488400000</REAL>
                                                                    </QUANTITY>
                                                                </VAR>
                                                                <VAR name = "NumSides">
                                                                    <INT>4</INT>
                                                                </VAR>
                                                                <VAR name = "Lattice">
                                                                    <STRING>&quot;Rectangular&quot;</STRING>
                                                                </VAR>
                                                                <VAR name = "Equilateral">
                                                                    <BOOL>true</BOOL>
                                                                </VAR>
                                                                <VAR name = "NumElementsX">
                                                                    <INT>16</INT>
                                                                </VAR>
                                                                <VAR name = "NumElementsY">
                                                                    <INT>16</INT>
                                                                </VAR>
                                                                <VAR name = "SpacingUnit">
                                                                    <STRING>&quot;Wavelength Ratio&quot;</STRING>
                                                                </VAR>
                                                                <VAR name = "SpacingX">
                                                                    <REAL>0.5</REAL>
                                                                </VAR>
                                                                <VAR name = "SpacingY">
                                                                    <REAL>0.5</REAL>
                                                                </VAR>
                                                            </SCOPE>
                                                        </VAR>
                                                    </VAR>
                                                    <VAR name = "Beamformer">
                                                        <VAR name = "Mvdr">
                                                            <SCOPE Class = "BeamFormer">
                                                                <VAR name = "Constraint">
                                                                    <QUANTITY Dimension = "RatioUnit" Unit = "units">
                                                                        <REAL>1.99526231496888</REAL>
                                                                    </QUANTITY>
                                                                </VAR>
                                                                <VAR name = "Type">
                                                                    <STRING>&quot;Mvdr&quot;</STRING>
                                                                </VAR>
                                                            </SCOPE>
                                                        </VAR>
                                                    </VAR>
                                                    <VAR name = "ShowGrid">
                                                        <BOOL>true</BOOL>
                                                    </VAR>
                                                    <VAR name = "ShowLabels">
                                                        <BOOL>true</BOOL>
                                                    </VAR>
                                                </SCOPE>
                                            </VAR>
                                        </VAR>
                                    </SCOPE>
                                </VAR>
                                <VAR name = "UsePolarization">
                                    <BOOL>false</BOOL>
                                </VAR>
                                <VAR name = "Polarization">
                                    <VAR name = "Linear">
                                        <SCOPE Class = "Polarization">
                                            <VAR name = "ReferenceAxis">
                                                <STRING>&quot;X Axis&quot;</STRING>
                                            </VAR>
                                            <VAR name = "TiltAngle">
                                                <QUANTITY Dimension = "AngleUnit" Unit = "rad">
                                                    <REAL>0</REAL>
                                                </QUANTITY>
                                            </VAR>
                                            <VAR name = "CrossPolLeakage">
                                                <QUANTITY Dimension = "RatioUnit" Unit = "units">
                                                    <REAL>1e-06</REAL>
                                                </QUANTITY>
                                            </VAR>
                                            <VAR name = "Type">
                                                <STRING>&quot;Linear&quot;</STRING>
                                            </VAR>
                                        </SCOPE>
                                    </VAR>
                                </VAR>
                                <VAR name = "Orientation">
                                    <VAR name = "Azimuth Elevation">
                                        <SCOPE Class = "Orientation">
                                            <VAR name = "AzimuthAngle">
                                                <QUANTITY Dimension = "AngleUnit" Unit = "rad">
                                                    <REAL>0</REAL>
                                                </QUANTITY>
                                            </VAR>
                                            <VAR name = "ElevationAngle">
                                                <QUANTITY Dimension = "AngleUnit" Unit = "rad">
                                                    <REAL>1.570796326794897</REAL>
                                                </QUANTITY>
                                            </VAR>
                                            <VAR name = "AboutBoresight">
                                                <STRING>&quot;Rotate&quot;</STRING>
                                            </VAR>
                                            <VAR name = "Type">
                                                <STRING>&quot;Azimuth Elevation&quot;</STRING>
                                            </VAR>
                                            <VAR name = "XPositionOffset">
                                                <QUANTITY Dimension = "SmallDistanceUnit" Unit = "m">
                                                    <REAL>0</REAL>
                                                </QUANTITY>
                                            </VAR>
                                            <VAR name = "YPositionOffset">
                                                <QUANTITY Dimension = "SmallDistanceUnit" Unit = "m">
                                                    <REAL>0</REAL>
                                                </QUANTITY>
                                            </VAR>
                                            <VAR name = "ZPositionOffset">
                                                <QUANTITY Dimension = "SmallDistanceUnit" Unit = "m">
                                                    <REAL>0</REAL>
                                                </QUANTITY>
                                            </VAR>
                                        </SCOPE>
                                    </VAR>
                                </VAR>
                            </SCOPE>
                        </VAR>
                    </SCOPE>
                </VAR>
            </VAR>
        </SCOPE>
    </VAR>
    <VAR name = "RFEnvironment">
        <SCOPE>
            <VAR name = "PropagationChannel">
                <SCOPE>
                    <VAR name = "UseITU618Section2p5">
                        <BOOL>false</BOOL>
                    </VAR>
                    <VAR name = "UseCloudFogModel">
                        <BOOL>false</BOOL>
                    </VAR>
                    <VAR name = "CloudFogModel">
                        <SCOPE Class = "LinkEmbedControl">
                            <VAR name = "ReferenceType">
                                <STRING>&quot;Unlinked&quot;</STRING>
                            </VAR>
                            <VAR name = "Component">
                                <VAR name = "ITU-R_P840-7">
                                    <SCOPE Class = "CloudFogLossModel">
                                        <VAR name = "Version">
                                            <STRING>&quot;1.0.0 a&quot;</STRING>
                                        </VAR>
                                        <VAR name = "IdentifierInformation">
                                            <SCOPE>
                                                <VAR name = "Identifier">
                                                    <STRING>&quot;{6EDBFDF1-16DD-4EAE-8B58-DEE30820B590}&quot;</STRING>
                                                </VAR>
                                                <VAR name = "Version">
                                                    <STRING>&quot;1&quot;</STRING>
                                                </VAR>
                                                <VAR name = "SourceIdentifierInformation">
                                                    <SCOPE>
                                                        <VAR name = "Identifier">
                                                            <STRING>&quot;{E7BA4392-37BE-4446-A5C7-6068165B166A}&quot;</STRING>
                                                        </VAR>
                                                        <VAR name = "Version">
                                                            <STRING>&quot;1&quot;</STRING>
                                                        </VAR>
                                                    </SCOPE>
                                                </VAR>
                                            </SCOPE>
                                        </VAR>
                                        <VAR name = "ComponentName">
                                            <STRING>&quot;ITU-R_P840-7&quot;</STRING>
                                        </VAR>
                                        <VAR name = "Description">
                                            <STRING>&quot;ITU-R P840-7&quot;</STRING>
                                        </VAR>
                                        <VAR name = "Type">
                                            <STRING>&quot;ITU-R P840-7&quot;</STRING>
                                        </VAR>
                                        <VAR name = "UserComment">
                                            <STRING>&quot;ITU-R P840-7&quot;</STRING>
                                        </VAR>
                                        <VAR name = "ReadOnly">
                                            <BOOL>false</BOOL>
                                        </VAR>
                                        <VAR name = "Clonable">
                                            <BOOL>true</BOOL>
                                        </VAR>
                                        <VAR name = "Category">
                                            <STRING>&quot;@Top&quot;</STRING>
                                        </VAR>
                                        <VAR name = "LiquidWaterDensityValueChoice">
                                            <STRING>&quot;Liquid Water Content Density Value&quot;</STRING>
                                        </VAR>
                                        <VAR name = "CloudCeiling">
                                            <QUANTITY Dimension = "DistanceUnit" Unit = "m">
                                                <REAL>3000</REAL>
                                            </QUANTITY>
                                        </VAR>
                                        <VAR name = "CloudLayerThickness">
                                            <QUANTITY Dimension = "DistanceUnit" Unit = "m">
                                                <REAL>500</REAL>
                                            </QUANTITY>
                                        </VAR>
                                        <VAR name = "CloudTemp">
                                            <QUANTITY Dimension = "Temperature" Unit = "K">
                                                <REAL>273.15</REAL>
                                            </QUANTITY>
                                        </VAR>
                                        <VAR name = "CloudLiqWaterDensity">
                                            <QUANTITY Dimension = "SmallDensity" Unit = "kg*m^-3">
                                                <REAL>0.0001</REAL>
                                            </QUANTITY>
                                        </VAR>
                                        <VAR name = "AnnualAveragePercentValue">
                                            <QUANTITY Dimension = "Percent" Unit = "unitValue">
                                                <REAL>0.01</REAL>
                                            </QUANTITY>
                                        </VAR>
                                        <VAR name = "MonthlyAveragePercentValue">
                                            <QUANTITY Dimension = "Percent" Unit = "unitValue">
                                                <REAL>0.01</REAL>
                                            </QUANTITY>
                                        </VAR>
                                        <VAR name = "LiqWaterAverageDataMonth">
                                            <INT>1</INT>
                                        </VAR>
                                        <VAR name = "UseRainHeightAsCloudThickness">
                                            <BOOL>false</BOOL>
                                        </VAR>
                                    </SCOPE>
                                </VAR>
                            </VAR>
                        </SCOPE>
                    </VAR>
                    <VAR name = "UseTropoScintModel">
                        <BOOL>false</BOOL>
                    </VAR>
                    <VAR name = "TropoScintModel">
                        <SCOPE Class = "LinkEmbedControl">
                            <VAR name = "ReferenceType">
                                <STRING>&quot;Unlinked&quot;</STRING>
                            </VAR>
                            <VAR name = "Component">
                                <VAR name = "ITU-R_P618-12">
                                    <SCOPE Class = "TropoScintLossModel">
                                        <VAR name = "Version">
                                            <STRING>&quot;1.0.0 a&quot;</STRING>
                                        </VAR>
                                        <VAR name = "IdentifierInformation">
                                            <SCOPE>
                                                <VAR name = "Identifier">
                                                    <STRING>&quot;{451EEC76-29A2-4831-9447-470F809996F8}&quot;</STRING>
                                                </VAR>
                                                <VAR name = "Version">
                                                    <STRING>&quot;1&quot;</STRING>
                                                </VAR>
                                                <VAR name = "SourceIdentifierInformation">
                                                    <SCOPE>
                                                        <VAR name = "Identifier">
                                                            <STRING>&quot;{BC27045B-5A54-458E-BF17-702BCFE40CA8}&quot;</STRING>
                                                        </VAR>
                                                        <VAR name = "Version">
                                                            <STRING>&quot;1&quot;</STRING>
                                                        </VAR>
                                                    </SCOPE>
                                                </VAR>
                                            </SCOPE>
                                        </VAR>
                                        <VAR name = "ComponentName">
                                            <STRING>&quot;ITU-R_P618-12&quot;</STRING>
                                        </VAR>
                                        <VAR name = "Description">
                                            <STRING>&quot;ITU-R P618-12&quot;</STRING>
                                        </VAR>
                                        <VAR name = "Type">
                                            <STRING>&quot;ITU-R P618-12&quot;</STRING>
                                        </VAR>
                                        <VAR name = "UserComment">
                                            <STRING>&quot;ITU-R P618-12&quot;</STRING>
                                        </VAR>
                                        <VAR name = "ReadOnly">
                                            <BOOL>false</BOOL>
                                        </VAR>
                                        <VAR name = "Clonable">
                                            <BOOL>true</BOOL>
                                        </VAR>
                                        <VAR name = "Category">
                                            <STRING>&quot;@Top&quot;</STRING>
                                        </VAR>
                                        <VAR name = "FadeDepthAverageTimeChoice">
                                            <STRING>&quot;Fade depth for the average year&quot;</STRING>
                                        </VAR>
                                        <VAR name = "ComputeDeepFade">
                                            <BOOL>false</BOOL>
                                        </VAR>
                                        <VAR name = "FadeOutage">
                                            <QUANTITY Dimension = "Percent" Unit = "unitValue">
                                                <REAL>0.001</REAL>
                                            </QUANTITY>
                                        </VAR>
                                        <VAR name = "PercentTimeRefracGrad">
                                            <QUANTITY Dimension = "Percent" Unit = "unitValue">
                                                <REAL>0.1</REAL>
                                            </QUANTITY>
                                        </VAR>
                                        <VAR name = "SurfaceTemperature">
                                            <QUANTITY Dimension = "Temperature" Unit = "K">
                                                <REAL>273.15</REAL>
                                            </QUANTITY>
                                        </VAR>
                                    </SCOPE>
                                </VAR>
                            </VAR>
                        </SCOPE>
                    </VAR>
                    <VAR name = "UseIonoFadingModel">
                        <BOOL>false</BOOL>
                    </VAR>
                    <VAR name = "IonoFadingModel">
                        <SCOPE Class = "LinkEmbedControl">
                            <VAR name = "ReferenceType">
                                <STRING>&quot;Unlinked&quot;</STRING>
                            </VAR>
                            <VAR name = "Component">
                                <VAR name = "ITU-R_P531-13">
                                    <SCOPE Class = "IonoFadingLossModel">
                                        <VAR name = "Version">
                                            <STRING>&quot;1.0.0 a&quot;</STRING>
                                        </VAR>
                                        <VAR name = "IdentifierInformation">
                                            <SCOPE>
                                                <VAR name = "Identifier">
                                                    <STRING>&quot;{A025F90F-68CC-407D-8025-C2E8918CC218}&quot;</STRING>
                                                </VAR>
                                                <VAR name = "Version">
                                                    <STRING>&quot;1&quot;</STRING>
                                                </VAR>
                                                <VAR name = "SourceIdentifierInformation">
                                                    <SCOPE>
                                                        <VAR name = "Identifier">
                                                            <STRING>&quot;{1699891E-9828-41C7-ADD4-4BE20EFC34A8}&quot;</STRING>
                                                        </VAR>
                                                        <VAR name = "Version">
                                                            <STRING>&quot;1&quot;</STRING>
                                                        </VAR>
                                                    </SCOPE>
                                                </VAR>
                                            </SCOPE>
                                        </VAR>
                                        <VAR name = "ComponentName">
                                            <STRING>&quot;ITU-R_P531-13&quot;</STRING>
                                        </VAR>
                                        <VAR name = "Description">
                                            <STRING>&quot;ITU-R P531-13&quot;</STRING>
                                        </VAR>
                                        <VAR name = "Type">
                                            <STRING>&quot;ITU-R P531-13&quot;</STRING>
                                        </VAR>
                                        <VAR name = "UserComment">
                                            <STRING>&quot;ITU-R P531-13&quot;</STRING>
                                        </VAR>
                                        <VAR name = "ReadOnly">
                                            <BOOL>false</BOOL>
                                        </VAR>
                                        <VAR name = "Clonable">
                                            <BOOL>true</BOOL>
                                        </VAR>
                                        <VAR name = "Category">
                                            <STRING>&quot;@Top&quot;</STRING>
                                        </VAR>
                                        <VAR name = "UseAlternateAPFile">
                                            <BOOL>false</BOOL>
                                        </VAR>
                                        <VAR name = "AlternateAPDataFile">
                                            <STRING>
                                                <PROP name = "FullName">
                                                    <STRING>&quot;&quot;</STRING>
                                                </PROP>&quot;&quot;</STRING>
                                        </VAR>
                                    </SCOPE>
                                </VAR>
                            </VAR>
                        </SCOPE>
                    </VAR>
                    <VAR name = "UseRainModel">
                        <BOOL>false</BOOL>
                    </VAR>
                    <VAR name = "RainModel">
                        <SCOPE Class = "LinkEmbedControl">
                            <VAR name = "ReferenceType">
                                <STRING>&quot;Unlinked&quot;</STRING>
                            </VAR>
                            <VAR name = "Component">
                                <VAR name = "ITU-R_P618-12">
                                    <SCOPE Class = "RainLossModel">
                                        <VAR name = "Version">
                                            <STRING>&quot;1.0.0 a&quot;</STRING>
                                        </VAR>
                                        <VAR name = "IdentifierInformation">
                                            <SCOPE>
                                                <VAR name = "Identifier">
                                                    <STRING>&quot;{48235919-70B3-4434-AED0-D40CD6C37A00}&quot;</STRING>
                                                </VAR>
                                                <VAR name = "Version">
                                                    <STRING>&quot;1&quot;</STRING>
                                                </VAR>
                                                <VAR name = "SourceIdentifierInformation">
                                                    <SCOPE>
                                                        <VAR name = "Identifier">
                                                            <STRING>&quot;{1113D770-D1E5-4DEF-99A3-6B3F4D5CE16A}&quot;</STRING>
                                                        </VAR>
                                                        <VAR name = "Version">
                                                            <STRING>&quot;1&quot;</STRING>
                                                        </VAR>
                                                    </SCOPE>
                                                </VAR>
                                            </SCOPE>
                                        </VAR>
                                        <VAR name = "ComponentName">
                                            <STRING>&quot;ITU-R_P618-12&quot;</STRING>
                                        </VAR>
                                        <VAR name = "Description">
                                            <STRING>&quot;ITU-R P618-12 rain model&quot;</STRING>
                                        </VAR>
                                        <VAR name = "Type">
                                            <STRING>&quot;ITU-R P618-12&quot;</STRING>
                                        </VAR>
                                        <VAR name = "UserComment">
                                            <STRING>&quot;ITU-R P618-12 rain model&quot;</STRING>
                                        </VAR>
                                        <VAR name = "ReadOnly">
                                            <BOOL>false</BOOL>
                                        </VAR>
                                        <VAR name = "Clonable">
                                            <BOOL>true</BOOL>
                                        </VAR>
                                        <VAR name = "Category">
                                            <STRING>&quot;@Top&quot;</STRING>
                                        </VAR>
                                        <VAR name = "SurfaceTemperature">
                                            <QUANTITY Dimension = "Temperature" Unit = "K">
                                                <REAL>273.15</REAL>
                                            </QUANTITY>
                                        </VAR>
                                        <VAR name = "EnableDepolarizationLoss">
                                            <BOOL>false</BOOL>
                                        </VAR>
                                    </SCOPE>
                                </VAR>
                            </VAR>
                        </SCOPE>
                    </VAR>
                    <VAR name = "UseAtmosAbsorptionModel">
                        <BOOL>false</BOOL>
                    </VAR>
                    <VAR name = "AtmosAbsorptionModel">
                        <SCOPE Class = "LinkEmbedControl">
                            <VAR name = "ReferenceType">
                                <STRING>&quot;Unlinked&quot;</STRING>
                            </VAR>
                            <VAR name = "Component">
                                <VAR name = "ITU-R_P676-9">
                                    <SCOPE Class = "AtmosphericAbsorptionModel">
                                        <VAR name = "Version">
                                            <STRING>&quot;1.0.1 a&quot;</STRING>
                                        </VAR>
                                        <VAR name = "IdentifierInformation">
                                            <SCOPE>
                                                <VAR name = "Identifier">
                                                    <STRING>&quot;{FD9EAF8E-4712-473B-AD5D-5D8E8CB59572}&quot;</STRING>
                                                </VAR>
                                                <VAR name = "Version">
                                                    <STRING>&quot;1&quot;</STRING>
                                                </VAR>
                                                <VAR name = "SourceIdentifierInformation">
                                                    <SCOPE>
                                                        <VAR name = "Identifier">
                                                            <STRING>&quot;{5DBDF434-D4CA-44F6-8097-A6EBF681200D}&quot;</STRING>
                                                        </VAR>
                                                        <VAR name = "Version">
                                                            <STRING>&quot;1&quot;</STRING>
                                                        </VAR>
                                                    </SCOPE>
                                                </VAR>
                                            </SCOPE>
                                        </VAR>
                                        <VAR name = "ComponentName">
                                            <STRING>&quot;ITU-R_P676-9&quot;</STRING>
                                        </VAR>
                                        <VAR name = "Description">
                                            <STRING>&quot;ITU-R P676-9 gaseous absorption model&quot;</STRING>
                                        </VAR>
                                        <VAR name = "Type">
                                            <STRING>&quot;ITU-R P676-9&quot;</STRING>
                                        </VAR>
                                        <VAR name = "UserComment">
                                            <STRING>&quot;ITU-R P676-9 gaseous absorption model&quot;</STRING>
                                        </VAR>
                                        <VAR name = "ReadOnly">
                                            <BOOL>false</BOOL>
                                        </VAR>
                                        <VAR name = "Clonable">
                                            <BOOL>true</BOOL>
                                        </VAR>
                                        <VAR name = "Category">
                                            <STRING>&quot;@Top&quot;</STRING>
                                        </VAR>
                                        <VAR name = "UseApproxMethod">
                                            <BOOL>true</BOOL>
                                        </VAR>
                                        <VAR name = "UseSeasonalRegional">
                                            <BOOL>true</BOOL>
                                        </VAR>
                                    </SCOPE>
                                </VAR>
                            </VAR>
                        </SCOPE>
                    </VAR>
                    <VAR name = "UseUrbanTerresPropLossModel">
                        <BOOL>false</BOOL>
                    </VAR>
                    <VAR name = "UrbanTerresPropLossModel">
                        <SCOPE Class = "LinkEmbedControl">
                            <VAR name = "ReferenceType">
                                <STRING>&quot;Unlinked&quot;</STRING>
                            </VAR>
                            <VAR name = "Component">
                                <VAR name = "Two_Ray">
                                    <SCOPE Class = "UrbanTerrestrialPropagationLossModel">
                                        <VAR name = "Version">
                                            <STRING>&quot;1.0.0 a&quot;</STRING>
                                        </VAR>
                                        <VAR name = "IdentifierInformation">
                                            <SCOPE>
                                                <VAR name = "Identifier">
                                                    <STRING>&quot;{260D7778-A1FA-4833-AABA-8D087758F2EE}&quot;</STRING>
                                                </VAR>
                                                <VAR name = "Version">
                                                    <STRING>&quot;1&quot;</STRING>
                                                </VAR>
                                                <VAR name = "SourceIdentifierInformation">
                                                    <SCOPE>
                                                        <VAR name = "Identifier">
                                                            <STRING>&quot;{60FA4C9B-5D74-4743-A449-66CEB6DFC97B}&quot;</STRING>
                                                        </VAR>
                                                        <VAR name = "Version">
                                                            <STRING>&quot;1&quot;</STRING>
                                                        </VAR>
                                                    </SCOPE>
                                                </VAR>
                                            </SCOPE>
                                        </VAR>
                                        <VAR name = "ComponentName">
                                            <STRING>&quot;Two_Ray&quot;</STRING>
                                        </VAR>
                                        <VAR name = "Description">
                                            <STRING>&quot;Two Ray (Fourth Power Law) atmospheric absorption model&quot;</STRING>
                                        </VAR>
                                        <VAR name = "Type">
                                            <STRING>&quot;Two Ray&quot;</STRING>
                                        </VAR>
                                        <VAR name = "UserComment">
                                            <STRING>&quot;Two Ray (Fourth Power Law) atmospheric absorption model&quot;</STRING>
                                        </VAR>
                                        <VAR name = "ReadOnly">
                                            <BOOL>false</BOOL>
                                        </VAR>
                                        <VAR name = "Clonable">
                                            <BOOL>true</BOOL>
                                        </VAR>
                                        <VAR name = "Category">
                                            <STRING>&quot;@Top&quot;</STRING>
                                        </VAR>
                                        <VAR name = "SurfaceTemperature">
                                            <QUANTITY Dimension = "Temperature" Unit = "K">
                                                <REAL>273.15</REAL>
                                            </QUANTITY>
                                        </VAR>
                                        <VAR name = "LossFactor">
                                            <REAL>1</REAL>
                                        </VAR>
                                    </SCOPE>
                                </VAR>
                            </VAR>
                        </SCOPE>
                    </VAR>
                    <VAR name = "UseCustomA">
                        <BOOL>false</BOOL>
                    </VAR>
                    <VAR name = "UseCustomB">
                        <BOOL>false</BOOL>
                    </VAR>
                    <VAR name = "UseCustomC">
                        <BOOL>false</BOOL>
                    </VAR>
                </SCOPE>
            </VAR>
        </SCOPE>
    </VAR>
    <VAR name = "LaserEnvironment">
        <SCOPE>
            <VAR name = "PropagationChannel">
                <SCOPE>
                    <VAR name = "EnableAtmosphericLossModel">
                        <BOOL>false</BOOL>
                    </VAR>
                    <VAR name = "AtmosphericLossModel">
                        <SCOPE Class = "LinkEmbedControl">
                            <VAR name = "ReferenceType">
                                <STRING>&quot;Unlinked&quot;</STRING>
                            </VAR>
                            <VAR name = "Component">
                                <VAR name = "Beer-Bouguer-Lambert_Law">
                                    <SCOPE Class = "LaserAtmosphericAbsorptionLossModel">
                                        <VAR name = "Version">
                                            <STRING>&quot;1.0.0 a&quot;</STRING>
                                        </VAR>
                                        <VAR name = "IdentifierInformation">
                                            <SCOPE>
                                                <VAR name = "Identifier">
                                                    <STRING>&quot;{84BC23F1-23CB-408D-816C-902EA19BB159}&quot;</STRING>
                                                </VAR>
                                                <VAR name = "Version">
                                                    <STRING>&quot;1&quot;</STRING>
                                                </VAR>
                                                <VAR name = "SourceIdentifierInformation">
                                                    <SCOPE>
                                                        <VAR name = "Identifier">
                                                            <STRING>&quot;{6896684B-630D-472D-8027-385684842E74}&quot;</STRING>
                                                        </VAR>
                                                        <VAR name = "Version">
                                                            <STRING>&quot;1&quot;</STRING>
                                                        </VAR>
                                                    </SCOPE>
                                                </VAR>
                                            </SCOPE>
                                        </VAR>
                                        <VAR name = "ComponentName">
                                            <STRING>&quot;Beer-Bouguer-Lambert_Law&quot;</STRING>
                                        </VAR>
                                        <VAR name = "Description">
                                            <STRING>&quot;Model atmospheric loss for laser receivers using the Beer-Bouguer-Lambert Law&quot;</STRING>
                                        </VAR>
                                        <VAR name = "Type">
                                            <STRING>&quot;Beer-Bouguer-Lambert Law&quot;</STRING>
                                        </VAR>
                                        <VAR name = "UserComment">
                                            <STRING>&quot;Model atmospheric loss for laser receivers using the Beer-Bouguer-Lambert Law&quot;</STRING>
                                        </VAR>
                                        <VAR name = "ReadOnly">
                                            <BOOL>false</BOOL>
                                        </VAR>
                                        <VAR name = "Clonable">
                                            <BOOL>true</BOOL>
                                        </VAR>
                                        <VAR name = "Category">
                                            <STRING>&quot;@Top&quot;</STRING>
                                        </VAR>
                                        <VAR name = "LayerList">
                                            <LIST>
                                                <SCOPE>
                                                    <VAR name = "LayerNum">
                                                        <INT>1</INT>
                                                    </VAR>
                                                    <VAR name = "LayerTop">
                                                        <QUANTITY Dimension = "DistanceUnit" Unit = "m">
                                                            <REAL>100000</REAL>
                                                        </QUANTITY>
                                                    </VAR>
                                                    <VAR name = "ExtinctionCoefficient">
                                                        <QUANTITY Dimension = "UnitlessPerSmallDistance" Unit = "m^-1">
                                                            <REAL>0</REAL>
                                                        </QUANTITY>
                                                    </VAR>
                                                </SCOPE>
                                            </LIST>
                                        </VAR>
                                        <VAR name = "EnableEvenlySpacedHeights">
                                            <BOOL>true</BOOL>
                                        </VAR>
                                        <VAR name = "MaxLayerHeight">
                                            <QUANTITY Dimension = "DistanceUnit" Unit = "m">
                                                <REAL>100000</REAL>
                                            </QUANTITY>
                                        </VAR>
                                    </SCOPE>
                                </VAR>
                            </VAR>
                        </SCOPE>
                    </VAR>
                    <VAR name = "EnableTropoScintLossModel">
                        <BOOL>false</BOOL>
                    </VAR>
                    <VAR name = "TropoScintLossModel">
                        <SCOPE Class = "LinkEmbedControl">
                            <VAR name = "ReferenceType">
                                <STRING>&quot;Unlinked&quot;</STRING>
                            </VAR>
                            <VAR name = "Component">
                                <VAR name = "ITU-R_P1814">
                                    <SCOPE Class = "LaserTropoScintLossModel">
                                        <VAR name = "Version">
                                            <STRING>&quot;1.0.0 a&quot;</STRING>
                                        </VAR>
                                        <VAR name = "IdentifierInformation">
                                            <SCOPE>
                                                <VAR name = "Identifier">
                                                    <STRING>&quot;{54E1D6A1-D1D7-4833-9255-B7CD79485236}&quot;</STRING>
                                                </VAR>
                                                <VAR name = "Version">
                                                    <STRING>&quot;1&quot;</STRING>
                                                </VAR>
                                                <VAR name = "SourceIdentifierInformation">
                                                    <SCOPE>
                                                        <VAR name = "Identifier">
                                                            <STRING>&quot;{651AF2C8-7D6D-457E-8F99-1FB796A460BF}&quot;</STRING>
                                                        </VAR>
                                                        <VAR name = "Version">
                                                            <STRING>&quot;1&quot;</STRING>
                                                        </VAR>
                                                    </SCOPE>
                                                </VAR>
                                            </SCOPE>
                                        </VAR>
                                        <VAR name = "ComponentName">
                                            <STRING>&quot;ITU-R_P1814&quot;</STRING>
                                        </VAR>
                                        <VAR name = "Description">
                                            <STRING>&quot;ITU-R P1814&quot;</STRING>
                                        </VAR>
                                        <VAR name = "Type">
                                            <STRING>&quot;ITU-R P1814&quot;</STRING>
                                        </VAR>
                                        <VAR name = "UserComment">
                                            <STRING>&quot;ITU-R P1814&quot;</STRING>
                                        </VAR>
                                        <VAR name = "ReadOnly">
                                            <BOOL>false</BOOL>
                                        </VAR>
                                        <VAR name = "Clonable">
                                            <BOOL>true</BOOL>
                                        </VAR>
                                        <VAR name = "Category">
                                            <STRING>&quot;@Top&quot;</STRING>
                                        </VAR>
                                        <VAR name = "AtmosphericTurbulenceModel">
                                            <VAR name = "Constant">
                                                <SCOPE Class = "AtmosphericTurbulenceModel">
                                                    <VAR name = "ConstantRefractiveIndexStructureParameter">
                                                        <REAL>1.7e-14</REAL>
                                                    </VAR>
                                                    <VAR name = "Type">
                                                        <STRING>&quot;Constant&quot;</STRING>
                                                    </VAR>
                                                </SCOPE>
                                            </VAR>
                                        </VAR>
                                    </SCOPE>
                                </VAR>
                            </VAR>
                        </SCOPE>
                    </VAR>
                </SCOPE>
            </VAR>
        </SCOPE>
    </VAR>
</SCOPE>
END Transmitter

BEGIN Extensions

    BEGIN ExternData
    END ExternData

    BEGIN ADFFileData
    END ADFFileData

    BEGIN AccessConstraints
        LineOfSight IncludeIntervals

        UsePreferredMaxStep No
        PreferredMaxStep 360
    END AccessConstraints

    BEGIN ObjectCoverage
    END ObjectCoverage

    BEGIN Desc
    END Desc

    BEGIN Refraction
        RefractionModel		 Effective Radius Method

        UseRefractionInAccess		 No

        BEGIN ModelData
            RefractionCeiling		  5.0000000000000000e+03
            MaxTargetAltitude		  1.0000000000000000e+04
            EffectiveRadius		  1.3333333333333299e+00

            UseExtrapolation		 Yes


        END ModelData
    END Refraction

    BEGIN Crdn
    END Crdn

    BEGIN Graphics

        BEGIN Graphics

            ShowGfx		 On
            Relative		 Off
            ShowBoresight		 On
            BoresightMarker		 4
            BoresightColor		 #ffffff

        END Graphics

        BEGIN DisplayTimes
            DisplayType		 AlwaysOn
        END DisplayTimes
    END Graphics

    BEGIN ContourGfx
        ShowContours		 Off
    END ContourGfx

    BEGIN Contours
        ActiveContourType		 Antenna Gain

        BEGIN ContourSet Antenna Gain
            Altitude		 0
            ShowAtAltitude		 Off
            Projected		 On
            Relative		 On
            ShowLabels		 Off
            LineWidth		 1
            DecimalDigits		 1
            ColorRamp		 On
            ColorRampStartColor		 #0000ff
            ColorRampEndColor		 #ff0000
            BEGIN ContourDefinition
                BEGIN CntrAntAzEl
                    CoordinateSystem		 0
                    BEGIN AzElPatternDef
                        SetResolutionTogether		 0
                        NumAzPoints		 181
                        AzimuthRes		 2
                        MinAzimuth		 -180
                        MaxAzimuth		 180
                        NumElPoints		 91
                        ElevationRes		 1
                        MinElevation		 0
                        MaxElevation		 90
                    END AzElPatternDef
                END CntrAntAzEl
            END ContourDefinition
        END ContourSet

        BEGIN ContourSet EIRP
            Altitude		 0
            ShowAtAltitude		 Off
            Projected		 On
            Relative		 On
            ShowLabels		 Off
            LineWidth		 1
            DecimalDigits		 1
            ColorRamp		 On
            ColorRampStartColor		 #0000ff
            ColorRampEndColor		 #ff0000
            BEGIN ContourDefinition
                BEGIN CntrAntAzEl
                    CoordinateSystem		 0
                    BEGIN AzElPatternDef
                        SetResolutionTogether		 0
                        NumAzPoints		 181
                        AzimuthRes		 2
                        MinAzimuth		 -180
                        MaxAzimuth		 180
                        NumElPoints		 91
                        ElevationRes		 1
                        MinElevation		 0
                        MaxElevation		 90
                    END AzElPatternDef
                END CntrAntAzEl
            END ContourDefinition
        END ContourSet

        BEGIN ContourSet Flux Density
            Altitude		 0
            ShowAtAltitude		 Off
            Projected		 On
            Relative		 On
            ShowLabels		 Off
            LineWidth		 1
            DecimalDigits		 1
            ColorRamp		 On
            ColorRampStartColor		 #0000ff
            ColorRampEndColor		 #ff0000
            BEGIN ContourDefinition
                BEGIN CntrAntLatLon
                    SetResolutionTogether		 true
                    Resolution		 1 1
                    ElevationAngleConstraint		 90
                    BEGIN LatLonSphGrid
                        Centroid		 0 0
                        ConeAngle		 0
                        NumPts		 181 91
                        Altitude		 0
                    END LatLonSphGrid
                END CntrAntLatLon
            END ContourDefinition
        END ContourSet

        BEGIN ContourSet RIP
            Altitude		 0
            ShowAtAltitude		 Off
            Projected		 On
            Relative		 On
            ShowLabels		 Off
            LineWidth		 1
            DecimalDigits		 1
            ColorRamp		 On
            ColorRampStartColor		 #0000ff
            ColorRampEndColor		 #ff0000
            BEGIN ContourDefinition
                BEGIN CntrAntLatLon
                    SetResolutionTogether		 true
                    Resolution		 1 1
                    ElevationAngleConstraint		 90
                    BEGIN LatLonSphGrid
                        Centroid		 0 0
                        ConeAngle		 0
                        NumPts		 181 91
                        Altitude		 0
                    END LatLonSphGrid
                END CntrAntLatLon
            END ContourDefinition
        END ContourSet

        BEGIN ContourSet Spectral Flux Density
            Altitude		 0
            ShowAtAltitude		 Off
            Projected		 On
            Relative		 On
            ShowLabels		 Off
            LineWidth		 1
            DecimalDigits		 1
            ColorRamp		 On
            ColorRampStartColor		 #0000ff
            ColorRampEndColor		 #ff0000
            BEGIN ContourDefinition
                BEGIN CntrAntLatLon
                    SetResolutionTogether		 true
                    Resolution		 1 1
                    ElevationAngleConstraint		 90
                    BEGIN LatLonSphGrid
                        Centroid		 0 0
                        ConeAngle		 0
                        NumPts		 181 91
                        Altitude		 0
                    END LatLonSphGrid
                END CntrAntLatLon
            END ContourDefinition
        END ContourSet
    END Contours

    BEGIN VO
    END VO

    BEGIN 3dVolume
        ActiveVolumeType		 Antenna Beam

        BEGIN VolumeSet Antenna Beam
            Scale		 4
            MinimumDisplayedGain		 1
            Frequency		 14500000000
            ShowAsWireframe		 0
            CoordinateSystem		 0
            BEGIN AzElPatternDef
                SetResolutionTogether		 0
                NumAzPoints		 181
                AzimuthRes		 2
                MinAzimuth		 -180
                MaxAzimuth		 180
                NumElPoints		 91
                ElevationRes		 1
                MinElevation		 0
                MaxElevation		 90
            END AzElPatternDef
            ColorMethod		 1
            MinToMaxStartColor		 #ff0000
            MinToMaxStopColor		 #0000ff
            RelativeToMaximum		 0
        END VolumeSet
        BEGIN VolumeGraphics
            ShowContours		 No
            ShowVolume		 No
        END VolumeGraphics
    END 3dVolume

END Extensions
