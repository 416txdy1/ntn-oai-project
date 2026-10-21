stk.v.12.0
WrittenBy    STK_v12.2.0

BEGIN Chain

    Name		 OAI_UL
    BEGIN Definition

        Object		 Place/OAI_UE/Transmitter/OAI_UE_UL_Tx
        Object		 Satellite/QIANFAN-166_69383/Receiver/OAI_SAT_UL_Rx
        Object		 Satellite/QIANFAN-166_69383/Transmitter/OAI_SAT_UL_Tx
        Object		 Place/Beijing/Receiver/OAI_gNB_UL_Rx
        Type		 Chain
        FromOperator		 Or
        FromOrder		 1
        ToOperator		 Or
        ToOrder		 1
        Recompute		 Yes
        IntervalType		 0
        ComputeIntervalStart		 0
        ComputeIntervalStop		 86400
        ComputeIntervalPtr		
        BEGIN EVENTINTERVAL
            BEGIN Interval
                Start		 28 Jul 2026 04:00:00.000000000
                Stop		 29 Jul 2026 04:00:00.000000000
            END Interval
            IntervalState		 Explicit
        END EVENTINTERVAL

        ConstConstraintsByStrands		 Yes
        UseSaveIntervalFile		 No
        SaveIntervalFile		 C:\Users\WSZ\.codex\visualizations\2026\07\24\019f9209-937f-7c50-8691-be0521d4eebc\STK_LEO_Constellation_20260923_train_v2\strand.int
        UseMinAngle		 No
        UseMaxAngle		 No
        UseMinLinkTime		 No
        LTDelayCriterion		 2
        TimeConvergence		 0.005
        AbsValueConvergence		 1e-14
        RelValueConvergence		 1e-08
        MaxTimeStep		 360
        MinTimeStep		 0.01
        UseLightTimeDelay		 Yes
        DetectEventsUsingSamplesOnly		 No
        UseLoadIntervalFile		 No
        BEGIN StrandObjIndexes
            StrandObj		 Place/OAI_UE/Transmitter/OAI_UE_UL_Tx
            StrandObj		 Satellite/QIANFAN-166_69383/Receiver/OAI_SAT_UL_Rx
            StrandObj		 Satellite/QIANFAN-166_69383/Transmitter/OAI_SAT_UL_Tx
            StrandObj		 Place/Beijing/Receiver/OAI_gNB_UL_Rx
        END StrandObjIndexes

        SaveMode		 1
        BEGIN StrandAccessesByIndex
            Strand		 0 1 2 3
            Start		  5.3340928080773083e+03
            Stop		  6.0802571698066577e+03
            Start		  1.1573501007819978e+04
            Stop		  1.2646327251786252e+04
            Start		  1.7956639385937826e+04
            Stop		  1.8848100063119637e+04
            Start		  4.8200263413941168e+04
            Stop		  4.8823275689060727e+04
            Start		  5.4234412163622867e+04
            Stop		  5.5291980189554088e+04
            Start		  6.0641656745450389e+04
            Stop		  6.1611904672332763e+04
        END StrandAccessesByIndex


    END Definition

    BEGIN Extensions

        BEGIN ExternData
        END ExternData

        BEGIN ADFFileData
        END ADFFileData

        BEGIN Desc
        END Desc

        BEGIN Crdn
        END Crdn

        BEGIN Graphics

            BEGIN Attributes

                StaticColor		 #00ffff
                AnimationColor		 #ff00ff
                AnimationLineWidth		 2
                StaticLineWidth		 3

            END Attributes

            BEGIN Graphics
                ShowGfx		 On
                ShowStatic		 Off
                ShowAnimationHighlight		 On
                ShowAnimationLine		 On
                ShowLinkDirection		 Off
            END Graphics
        END Graphics

        BEGIN VO
        END VO

    END Extensions

END Chain

