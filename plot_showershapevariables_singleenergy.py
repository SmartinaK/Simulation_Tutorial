import uproot
import awkward as ak
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages



pi0_file = uproot.open("ALLEGRO_RECO_1000evt_50GeV_pi0_theta90_stripseverywhere.root")
photon_file = uproot.open("ALLEGRO_RECO_1000evt_50GeV_photon_theta90_stripseverywhere.root")

pi0_tree = pi0_file["events"]
photon_tree = photon_file["events"]


# Shower shape varibales are stored in the _shapeParameters vector. Every cluster has 189 entries: 17 variables * 11 layers + 2 extra values. In the following, we are filtering events with only one 
# reconstructed cluster, define the offset of 6 variables (layer 1). The same variable for the next layer is therefore accessed by steps of 17 
pi0_show_shape_branch = pi0_tree["_AugmentedEMBCaloClusters_shapeParameters"].array(library="ak")
photon_show_shape_branch = photon_tree["_AugmentedEMBCaloClusters_shapeParameters"].array(library="ak")

# Filter events with exactly 189 entries (corresponds to events with only one reconstructed cluster)
mask_pi0 = ak.num(pi0_show_shape_branch, axis=1) == 189
mask_photon = ak.num(photon_show_shape_branch, axis=1) == 189

flat_pi0_show_shape_branch = ak.flatten(pi0_show_shape_branch[mask_pi0])
flat_photon_show_shape_branch = ak.flatten(photon_show_shape_branch[mask_photon])

# Define variable offsets per layer
offsets = {
    "Eratio": 6,
    "DeltaE": 7,
    "phi_Eratio": 8,
    "phi_DeltaE": 9,
    "fsidepm3": 15,
    "fsidepm4": 16,
}
layer_step = 17
layers = range(1, 12)  # 11 layers

# Extracting the variables per layer
def extract_variables(flat_array):
    data = {}
    for layer in layers:
        for var, base_offset in offsets.items():
            idx = base_offset + (layer - 1) * layer_step
            data[f"{var}_{layer}"] = flat_array[idx::189]
    return data

pi0_vars = extract_variables(flat_pi0_show_shape_branch)
photon_vars = extract_variables(flat_photon_show_shape_branch)

# Normalize histograms
bins = np.linspace(0, 1.03, 50)
bin_centers = (bins[:-1] + bins[1:]) / 2

def get_histogram(data, bins):
    hist, _ = np.histogram(data, bins=bins)
    return hist / np.sum(hist)

def compute_histograms(vars_dict):
    return {k: get_histogram(v, bins) for k, v in vars_dict.items()}

pi0_hists = compute_histograms(pi0_vars)
photon_hists = compute_histograms(photon_vars)

  
  
def plot_layer(layer_num, bin_centers, bins, pi0_vars, photon_vars, pi0_hists, photon_hists):
    fig, axs = plt.subplots(2, 3, figsize=(18, 12))

    # Each subplot: (variable name, xlim, xlabel, title)
    plot_configs = [
        ("Eratio",    (0, 1.01), "Energy Ratio", "Energy Ratio"),
        ("DeltaE",    (0, 1.03), r"$\Delta$_E [GeV]", r"$\Delta$_E"),
        ("fsidepm3",  (0, 1.03), "$F_{side}$", "$F_{side}\pm 3$"),
        ("phi_Eratio",(0, 1.03), "Energy Ratio", "Energy Ratio in phi"),
        ("phi_DeltaE",(0, 1.03), r"$\Delta$_E [GeV]", r"$\Delta$_E in phi"),
        ("fsidepm4",  (0, 1.03), "$F_{side}$", "$F_{side}\pm 4$"),
    ]

    for ax, (var, xlim, xlabel, title) in zip(axs.flat, plot_configs):
        key = f"{var}_{layer_num}"
        pi0_hist = pi0_hists[key]
        photon_hist = photon_hists[key]
        pi0_entries = pi0_vars[key]
        photon_entries = photon_vars[key]

        # Plot normalized histograms
        ax.hist(bin_centers, bins=bins, weights=pi0_hist,
                color='blue', alpha=0.35, edgecolor='mediumblue', linewidth=1.7,
                label=r'$\pi^{0}$', histtype='stepfilled')
        ax.hist(bin_centers, bins=bins, weights=photon_hist,
                color='yellow', alpha=0.42, edgecolor='gold', linewidth=1.7,
                label=r'$\gamma$', histtype='stepfilled')

        ax.set_xlim(*xlim)
        ax.set_yscale("log")
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Fraction of Entries per Bin")
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Add entry counts (number of events used per file that had one cluster)
        ax.text(0.42, 0.84,
                f"Entries\n$\\pi^0$: {len(pi0_entries)}\n$\\gamma$: {len(photon_entries)}",
                transform=ax.transAxes, fontsize=10,
                bbox=dict(facecolor='white', alpha=0.6, edgecolor='grey'))

    fig.suptitle(f"Layer {layer_num}, 50GeV", fontsize=16)
    return fig

# Save plots in multipage pdf file
with PdfPages("50GeV_Filtered_AllLayers.pdf") as pdf:
    for layer in range(1, 12):
        fig = plot_layer(layer, bin_centers, bins, pi0_vars, photon_vars, pi0_hists, photon_hists)
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)
