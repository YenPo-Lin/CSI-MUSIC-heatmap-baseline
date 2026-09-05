import numpy as np
import pre_processing as pp
import MUSIC
import time




def signal_processing(raw_CSI, args):

    start_preprocessing = time.time()
    CSI = pp.self_sanitize(raw_CSI) # = np.abs(raw_CSI) # remove NaN and Inf
    background = pp.MA(CSI, args.fs * 0.5)

    if args.preprocess == "ma":
        CSI = (CSI - background) # Original Version
        #CSI = (CSI - background) / (background + 1e-8) # Normalized dynamic residual
    elif args.preprocess == "dwt":
        CSI = pp.DWT_components(CSI, target_labels= ["", "D5", "D4", "D3", "D2", ""])
    elif args.preprocess == "pca":
        CSI  -= background
        CSI = pp.PCA_time(CSI, args.fs *0.5, k=3)

    #CSI = np.mean(CSI, axis=1, keepdims=True) # average over Tx

    # Re sampling
    # CSI = pp.sample_subcarriers(args, CSI, freq_space=args.freq_space)

    end_preprocessing = time.time()
    print(f"Preprocessing Method: {args.preprocess} | Time: {end_preprocessing - start_preprocessing:.2f}s")


    tof_dop = MUSIC.ToF_Dop(args)
    azi_tof = MUSIC.Azi_ToF(args)
    azi_dop = MUSIC.Azi_Dop(args)
    azi_tof_dop = MUSIC.Azi_ToF_Dop(args)

    
    frame_idx = args.frame_idx

    print(f"Processing Frame {frame_idx}... ")
    azi_tof.gen_spectrum(CSI, frame_idx, x_axis="azi", y_axis="tof")
    tof_dop.gen_spectrum(CSI, frame_idx, x_axis="doppler", y_axis="tof")
    azi_dop.gen_spectrum(CSI, frame_idx, x_axis="azi", y_axis="doppler")
    azi_tof_dop.gen_spectrum(CSI, frame_idx)





    
