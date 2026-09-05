# CSI-MUSIC Heatmap Baseline

- Azimuth–ToF（方位角–飛行時間）
- ToF–Doppler（飛行時間–都卜勒頻率）
- Azimuth–Doppler（方位角–都卜勒頻率）
- Azimuth–ToF–Doppler 3D MUSIC，並投影成上述三種 2D heatmap

> 注意：目前的前處理會將複數 CSI 轉為振幅，因此輸出應理解為「振幅域 MUSIC pseudo-spectrum」，不是保留跨天線複數相位的標準 coherent MUSIC。

## 1. 專案檔案

```text
.
├── main.py                 # 程式入口與參數設定
├── signal_processing.py    # 前處理及各 MUSIC 模組的執行流程
├── pre_processing.py       # MA、DWT、PCA 等前處理
├── MUSIC.py                # Steering vector、covariance 與 MUSIC 計算
├── Plot.py                 # Heatmap 繪圖與存檔
└── 20260820-172856_move_fb.npz  # 範例 CSI 資料
```

## 2. 環境安裝

建議使用 Python 3，並在虛擬環境中安裝套件：

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install numpy scipy matplotlib PyWavelets tqdm
```

## 3. 輸入資料格式

輸入檔案需為 `.npz`，且第一個陣列必須是 CSI，shape 為：

```text
(num_frames, num_Tx, num_Rx, num_subcarriers)
```

本專案附帶的範例資料中：

```text
csi.shape = (982, 2, 8, 64)
```

各維度依序代表：

- `982`：frame 數量
- `2`：Tx 數量
- `8`：Rx 數量
- `64`：subcarrier 數量

## 4. 快速執行

直接使用預設資料與參數：

```bash
python3 main.py
```

程式完成後會用 Matplotlib 顯示 heatmap。預設分析第 `660` 個 frame。
若要生成多張圖請自記寫loop 並且設定 pics_dir 圖片儲存位置

若要把圖片存到資料夾：

```bash
python3 main.py --pics_dir results
```

`results/` 內會產生：

```text
Azimuth-ToF 0660.png
ToF-Doppler 0660.png
Azimuth-Doppler 0660.png
0660_azi_tof_dop_sum.png
```

使用自己的 CSI 檔案：

```bash
python3 main.py --csi_file your_csi.npz --frame_idx 500 --pics_dir results
```

查看全部參數：

```bash
python3 main.py --help
```

## 5. 常用參數

| 參數 | 預設值 | 說明 |
| --- | ---: | --- |
| `--csi_file` | 範例 `.npz` | CSI 資料路徑 |
| `--frame_idx` | `660` | 要分析的中心 frame |
| `--fs` | `100` | CSI frame rate，單位 Hz |
| `--f_0` | `5.57e9` | WiFi 中心頻率，單位 Hz |
| `--delta_f` | `2.54e6` | 使用中的相鄰 subcarrier 頻率間距，單位 Hz |
| `--antenna_spacing` | `0.02` | 相鄰 Rx 天線距離，單位 m |
| `--preprocess` | `ma` | 前處理方法：`ma`、`dwt` 或 `pca` |
| `--Sdim` | `3` | MUSIC signal subspace 維度 |
| `--projection` | `cos` | Azimuth steering model：`cos` 或 `sin` |
| `--theta_min/max/step` | `0/180/3` | Azimuth 搜尋範圍，單位 degree |
| `--tau_min/max/step` | `2e-9/15e-9/3e-10` | ToF 搜尋範圍，單位 second |
| `--doppler_min/max/step` | `-20/20/1` | Doppler 搜尋範圍，單位 Hz |
| `--pics_dir` | `None` | 圖片輸出資料夾；未設定時只顯示圖片 |

其中：

- `stream_win` 控制 Rx 空間 aperture 大小。
- `freq_win` 與 `freq_hop` 控制 subcarrier frequency aperture。
- `time_win` 控制 Doppler steering 使用的時間 aperture。
- `avg_frames` 是 Azimuth–ToF covariance 使用的時間範圍。
- `time_sample_range` 是含 Doppler 模組建立滑動 snapshots 的時間範圍。

這些 window 參數不可超過實際 CSI 的 Rx、subcarrier 或 frame 數量。

## 6. 處理流程

```text
讀取 .npz CSI
    ↓
CSI 複數值轉為振幅
    ↓
MA / DWT / PCA 前處理
    ↓
空間、頻率、時間 smoothing，建立 covariance matrix
    ↓
MUSIC eigendecomposition 與 grid search
    ↓
轉為 dB 並繪製 heatmap
```

預設 `ma` 會計算約 `0.5 秒` 的 moving average background，再以 `CSI - background` 取得動態振幅成分。

## 7. 注意事項

- 執行 3D MUSIC 需要較多計算時間；縮小 Azimuth、ToF 或 Doppler 搜尋範圍可加快測試。
- `Sdim` 代表假設的 signal 數量／signal subspace 維度，應依資料與場景調整。
- `projection=sin` 或 `cos` 必須符合實際天線幾何與角度定義。
- 若使用自己的資料，請同步確認 `fs`、`f_0`、`delta_f`、天線間距與天線順序。
- `axis=m` 只會把 ToF 圖軸換算為距離：`distance = ToF × c / 2`。
- 目前 `signal_processing.py` 會一次執行全部四種結果，尚未提供只選擇單一 MUSIC 模組的命令列參數。

## 8. 縮小網格的快速測試

若只想確認環境與流程能否正常執行，可先使用較小的搜尋網格：

```bash
python3 main.py \
  --frame_idx 100 \
  --stream_win 2 \
  --freq_win 6 \
  --freq_hop 3 \
  --freq_sample_range 8 \
  --time_win 3 \
  --time_sample_range 5 \
  --avg_frames 5 \
  --theta_min 0 \
  --theta_max 6 \
  --theta_step 3 \
  --tau_min 2e-9 \
  --tau_max 2.6e-9 \
  --tau_step 3e-10 \
  --doppler_min -1 \
  --doppler_max 1 \
  --doppler_step 1 \
  --pics_dir /tmp/csi_music_smoke_test
```
# CSI-MUSIC-heatmap-baseline
