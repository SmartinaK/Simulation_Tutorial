# Simulation_Tutorial
Scripts and description on how to run ALLEGRO ECal simulation, do energy response/resolution and shower shape variables studies 

TUTORIAL

Further instructions can be also found here https://github.com/HEP-FCC/FCC-config/tree/main/FCCee/FullSim/ALLEGRO/ALLEGRO_o1_v03 and here https://hep-fcc.github.io/fcc-tutorials/master/full-detector-simulations/FccCaloPerformance/CaloFullSimExercise.html

The first step is to source key4hep by using:

source /cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh

If you want to source a specific (stable) version, you can add > -r <release date> , e.g.

source /cvmfs/sw.hsf.org/key4hep/setup.sh -r 2025-05-29

If the k4geo library is installed locally and should be inclued instead, one has to go to the directory where k4ge0 is installed and set the environment variable
export K4GEO=$PWD/k4geo/

Here is more information on how to set up paths to your local installation: https://fccsw.web.cern.ch/fccsw/filesForSimDigiReco/ALLEGRO/ALLEGRO_o1_v03/

Then you can run the simulation with ddsim, by putting this directly in the terminal:

ddsim --enableGun --gun.phiMin "89*deg" --gun.phiMax "91*deg" --gun.thetaMin "89*deg" --gun.thetaMax "91*deg" --gun.distribution uniform --gun.energy "1*GeV" --gun.particle gamma --numberOfEvents 100 --outputFile /eos/user/m/mkoppitz/Public/output_simulations/new_setup_v03/10kruns/ALLEGRO_sim_test_nostrips.root --random.enableEventSeed --random.seed 42 --compactFile $K4GEO/FCCee/ALLEGRO/compact/ALLEGRO_o1_v03/ALLEGRO_o1_v03.xml 

It initiates the detector simulation tool ddsim, and by adding all the input arguments behind you directly steer and modify what type of simulation you want it to do. The modus (particle gun, meaning you shot particles into the detector), the distribution (unifrom means it shots them into the detector uniformly, it is possible to set it to a fixed angle and only shoot particles into one direction), energy, particle type (e- for electrons, gamma for photons, pi0 for neutral pions etc.), number of events (take for the start 100), name of your outputfile.
The random seed and sets it to 42. This is a parameter that is being used by the simulation to initialize its random number generator to generate the events. Keep it same for all following simulations to guarantee reproducibility and be able to compare different runs. The --compactfile points to the location and file that contains the geometry description of the detector. Since you only source key4hep from the central stack, it will take this file from there directly.


Once the simulation is done, an output root file has been created. Now the digitization and reconstruction has to be run using the steering file run_dogo_reco.py. It calls the tools necessary for the individual steps, the user can choose which reconstruction algorithm to use (sliding window and/or topoclustering), add noise, magentic field etc...
Files like neighbouring maps can be downloaded here: https://fccsw.web.cern.ch/fccsw/filesForSimDigiReco/ALLEGRO/ALLEGRO_o1_v03/ . Note: If you change the segmentation in your studies, noise and neighbouring maps need to be regnenerated!

The reconstructioin can now be run using k4run run_digo_reco.py . The output root file contains collections with the propoerties of the simulated process, reconstructed energies, shower shape variables, momenta etc. 

