#!/usr/bin/env python3
"""
compute_energy_res.py
Compute calorimeter energy response & resolution for one or more
cluster-energy branches and plot them on the same canvas.

Default branches:
    - AugmentedEMBCaloClusters.energy - Sliding window algorithm for reconstruction
    - AugmentedEMBCaloTopoClusters.energy - Topoclustering
"""

import argparse, csv, glob, re
from math import sqrt

import numpy as np
import ROOT

# Extract truth energy from file name. My files are named with the same pattern, only the energy value varies 

def truth_energy_from_name(fname: str) -> float:

    m = re.search(r'_pMin_([0-9]+)', fname)
    if m:
        return float(m.group(1)) / 1000.0

    m = re.search(r'_energy_([0-9]+)', fname)
    if m:
        return float(m.group(1)) / 1000.0

    m = re.search(r'_([0-9]+)GeV', fname)
    if m:
        return float(m.group(1))

    raise RuntimeError(f"Cannot deduce truth energy from: {fname}")



# Read single files to later compute response and resolution for the whole energy range
# From the events tree, we extract the clusters per event. The threshold of 0.1 is mainly for the toposluster clusters, since we observe many satellite clusters with low energies here after reconstruction that need to be excluded in the analysis 

def process_one_file(fname: str, branch: str):

    Etrue = truth_energy_from_name(fname)

    df = ROOT.RDataFrame("events", fname)
    df = (df
          .Alias("clE", branch)
          .Define("good_cl", "clE[clE>0.1]")
          .Filter("good_cl.size()>0")
          .Define("lead_idx", "ArgMax(good_cl)")
          .Define("resp", f"(good_cl[lead_idx] - {Etrue})/{Etrue}")
    )

    half_range = 0.30 * sqrt(1./Etrue + 1.5)
    hist = df.Histo1D(("h", "", 600, -half_range, +half_range), "resp")

    mu0, sig0 = hist.GetMean(), hist.GetStdDev()
    fit = hist.Fit("gaus", "Q0S", "", mu0 - 2*sig0, mu0 + 2*sig0)
    mu    = fit.Parameter(1)
    sigma = fit.Parameter(2) / (1.0 + mu)

    return Etrue, mu, sigma, hist



# ----------------------------------------------------------------------
# Parser to modify input and output parameters

def main():
    parser = argparse.ArgumentParser(
        description="Compute energy response & resolution for several cluster collections")

    parser.add_argument("indir", nargs="?", help="Directory that holds the input *.root files")
    parser.add_argument("-i", "--indir", dest="indir_opt",
                        help="Same as positional <indir> but as a flag")
    parser.add_argument("-o", "--csv", default="energy_perf_LArPb.csv",
                        help="CSV output file")
    parser.add_argument("-p", "--png", default="energy_perf_LArPb.png",
                        help="PNG canvas with response & resolution graphs")
    parser.add_argument("-b", "--branches", nargs="+", metavar="BRANCH",
                        default=["AugmentedEMBCaloClusters.energy",
                                 "AugmentedEMBCaloTopoClusters.energy"],
                        help="Space-separated list of branch names to analyse")
    parser.add_argument("-P", "--pattern",
                        default="ALLEGRO_RECO_1000evt_*GeV_photon_stripseverywhere_LAr_Pb.root",
                        help="Filename pattern used to pick ROOT files")

    args = parser.parse_args()

    indir = args.indir_opt or args.indir
    if not indir:
        parser.error("Indicate the directory with -i/--indir")

    ROOT.gROOT.SetBatch(True)
    ROOT.EnableImplicitMT()
    ROOT.gStyle.SetOptStat(0)
    ROOT.gStyle.SetOptFit(0)

    files = glob.glob(f"{indir}/{args.pattern}")
    files.sort(key=truth_energy_from_name)
    if not files:
        raise RuntimeError("No ROOT files matched the pattern.")

    print("Files to be processed:")
    for f in files:
        print("  ", f)

    # multi-collection analysis
    results = {}  # branch → dict(E,R,S)
    for branch in args.branches:
        Es, Rs, Ss = [], [], []
        for f in files:
            E, R, S, _ = process_one_file(f, branch)
            Es.append(E)
            Rs.append(R)
            Ss.append(S)
        results[branch] = dict(E=Es, R=Rs, S=Ss)

    # write combined CSV
    with open(args.csv, "w", newline="") as fp:
        wr = csv.writer(fp)
        wr.writerow(["ClusterType", "E_truth_GeV", "response_mean", "resolution_sigma_over_E", "NeventsPass"])
        for br, d in results.items():
            for E, R, S in zip(d["E"], d["R"], d["S"]):
                wr.writerow([br, E, R, S, 1_000_000])
    print(f"CSV written to {args.csv}")

    # draw curves
    graphs_resp = []
    graphs_resol = []

    marker_styles = [20, 21, 22, 23, 24, 25]
    colors = [1, 2, 4, 6, 8, 9]

    can = ROOT.TCanvas("c", "c", 800, 800)
    can.Divide(1, 2)
    
    # energy response
    can.cd(1)
    frame1 = ROOT.TH1F("frame1", "Energy response;Truth energy [GeV];#LT(E_{rec}-E_{true})/E_{true}#GT", 100, 0, 110)
    frame1.SetMinimum(-0.1)
    frame1.SetMaximum(+0.1)
    frame1.Draw()

    leg_resp = ROOT.TLegend(0.15, 0.75, 0.45, 0.88)

    for i, (br, d) in enumerate(results.items()):
        g = ROOT.TGraph(len(d["E"]),
                        np.array(d["E"], dtype='d'),
                        np.array(d["R"], dtype='d'))
        col = colors[i % len(colors)]
        g.SetMarkerStyle(marker_styles[i % len(marker_styles)])
        g.SetMarkerColor(col)
        g.SetLineColor(col)
        g.SetTitle("Energy response;Truth energy [GeV];#LT(E_{rec}-E_{true})/E_{true}#GT")
        g.Draw("P SAME")

        leg_resp.AddEntry(g, br, "pl")
        graphs_resp.append(g)

    leg_resp.Draw()

    # energy resolution
    can.cd(2)
    frame2 = ROOT.TH1F("frame2", "Energy resolution;Truth energy [GeV];#sigma_{E}/E", 100, 0, 110)
    frame2.SetMinimum(0)
    frame2.SetMaximum(0.6)
    frame2.Draw()

    leg_res = ROOT.TLegend(0.15, 0.75, 0.45, 0.88)

    for i, (br, d) in enumerate(results.items()):
        g = ROOT.TGraph(len(d["E"]),
                        np.array(d["E"], dtype='d'),
                        np.array(d["S"], dtype='d'))
        col = colors[i % len(colors)]
        g.SetMarkerStyle(marker_styles[i % len(marker_styles)])
        g.SetMarkerColor(col)
        g.SetLineColor(col)
        g.SetTitle("Energy resolution;Truth energy [GeV];#sigma_{E}/E")
        g.Draw("P SAME")

        leg_res.AddEntry(g, br, "pl")
        graphs_resol.append(g)

    leg_res.Draw()
    can.SaveAs(args.png)
    print(f"PNG written to {args.png}")

# ----------------------------------------------------------------------
if __name__ == "__main__":
    main()
