import os
import time
import argparse
import numpy as np
import matplotlib.pyplot as plt
from signal_processing import signal_processing



def create_parser():
    parser = argparse.ArgumentParser()

    # npz 文件路徑
    file_path = "20260820-172856_move_fb.npz"
    parser.add_argument('--csi_file', type=str, default=file_path)
    
    # ---- CSI parameters ----
    parser.add_argument('--f_0', type=float, default=5.57e9)
    parser.add_argument('--BW', type=float, default=160e6)
    parser.add_argument('--delta_f', type=float, default=2.54e6) 
    # 160 M /2024 = 79.05 kHz 
    # 160 M /63 =  2.54 MHz
    parser.add_argument('--fs', type=int, default=100)
    parser.add_argument('--antenna_spacing', type=float, default=0.02)
    
    # ---- MUSIC settings ----
    parser.add_argument('--preprocess', type=str, default='ma', choices=['ma', 'dwt', 'pca'])
    # plotted frame
    parser.add_argument('--frame_idx', type=int, default=660)
    # MUSIC signal dimension
    parser.add_argument('--Sdim', type=int, default=3)
    parser.add_argument('--Sdim_energy_ratio', type=float, default=0.66)
    parser.add_argument('--avg_frames', type=int, default=50)
    parser.add_argument('--projection', type=str, default='cos', choices=['sin', 'cos'])

    parser.add_argument('--stream_win', type=int, default=5)
    parser.add_argument('--stream_sample_range', type=int, default=8) #all Rx

    parser.add_argument('--freq_win', type=int, default=48) #block size = freq_win // freq_hop
    parser.add_argument('--freq_hop', type=int, default=3)
    parser.add_argument('--freq_sample_range', type=int, default=64) #all subcarriers
    parser.add_argument('--freq_space', type=int, default=1) # if freq resampling


    parser.add_argument('--time_win', type=int, default=20)
    parser.add_argument('--time_hop', type=int, default=1)
    parser.add_argument('--time_sample_range', type=int, default=50) #100 frames

    # Azimuth grid
    parser.add_argument('--theta_min', type=float, default= 0)
    parser.add_argument('--theta_max', type=float, default= 180)
    parser.add_argument('--theta_step', type=int, default=3)
    # Time of Flight grid
    parser.add_argument('--axis', type=str, default='ns', choices=['ns', 'm'])
    parser.add_argument('--tau_min', type=float, default=2e-9)
    parser.add_argument('--tau_max', type=float, default=15e-9)
    parser.add_argument('--tau_step', type=float, default=3e-10)
    # Doppler grid
    parser.add_argument('--doppler_min', type=float, default=-20)
    parser.add_argument('--doppler_max', type=float, default=20)
    parser.add_argument('--doppler_step', type=float, default=1)

    # Doppler spectrogram settings
    parser.add_argument('--stft_nperseg', type=int, default=64)
    parser.add_argument('--stft_noverlap', type=int, default=63) # hop 1

    # heatmap axis (X: Azi, Y: TOF if True)
    parser.add_argument('--axis_flip', type=bool, default=True)
    parser.add_argument('--colorbar', type=bool, default=True)
    
    # ---- 圖片保存路徑 ----
    parser.add_argument('--pics_dir', type=str, default=None)
 
    return parser


if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()

    if not os.path.isfile(args.csi_file):
        raise FileNotFoundError(f"❌ 找不到 CSI 檔案: {args.csi_file}")
    else:
        # ---- Load CSI ----
        print(f"📁 LOADING: {os.path.basename(args.csi_file)}")
        data = np.load(args.csi_file)
        CSI = data[data.files[0]]

        # ---- Read CSI dimensions ----
        args.num_frames, args.num_Tx, args.num_Rx, args.num_sc = CSI.shape
        print(f"✅ CSI{CSI.shape} | Frames:{args.num_frames/args.fs:.2f}s | Fs:{args.fs}Hz")

    print("🥶 Start Signal Processing...")

    start = time.time()
    signal_processing(CSI, args)
    elapsed_time = time.time() - start
    print(f"🥶 End Signal Processing: {elapsed_time:.2f} (s)")

    plt.show()
