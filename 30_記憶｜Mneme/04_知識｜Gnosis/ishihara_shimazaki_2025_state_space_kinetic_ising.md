State-space kinetic Ising model reveals task-dependent entropy flow in sparsely active
nonequilibrium neuronal dynamics
Ken Ishihara1,2∗ Hideaki Shimazaki2,3†
1

arXiv:2502.15440v3 [q-bio.NC] 11 Dec 2025

Graduate School of Life Science, Hokkaido University, Sapporo,
Japan. 2 Center for Human Nature, Artificial Intelligence,
and Neuroscience (CHAIN), Hokkaido University, Sapporo, Japan.
3
Graduate School of Informatics, Kyoto University, Kyoto, Japan
Neuronal ensemble activity, including coordinated and oscillatory patterns, exhibits hallmarks of
nonequilibrium systems with time-asymmetric trajectories to maintain their organization. However,
assessing time asymmetry from neuronal spiking activity remains challenging. The kinetic Ising
model provides a framework for studying the causal, nonequilibrium dynamics in spiking recurrent
neural networks. Recent theoretical advances in this model have enabled time-asymmetry estimation
from large-scale steady-state data. Yet, neuronal activity often exhibits time-varying firing rates and
coupling strengths, violating the steady-state assumption. To overcome this limitation, we developed
a state-space kinetic Ising model that accounts for nonstationary and nonequilibrium properties of
neural systems. This approach incorporates a mean-field method for estimating time-varying entropy
flow, a key measure for maintaining the system’s organization through dissipation. Applying this
method to mouse visual cortex data revealed greater variability in causal couplings during task
engagement despite reduced neuronal activity with increased sparsity. Moreover, higher-performing
mice exhibited increased coupling-related entropy flow per spike during task engagement, suggesting
more efficient computation in the higher-performing mice. These findings underscore the model’s
utility in uncovering intricate asymmetric causal dynamics in neuronal ensembles and linking them
to behavior through the thermodynamic underpinnings of neural computation.

INTRODUCTION

The emergence of ordered spatiotemporal dynamics in
nonequilibrium systems that continuously exchange energy and matter with their surroundings has intrigued
many scientists [1–5], as it provides a foundational mechanism for phenomena such as chemical oscillations, morphogenesis, and collective behaviors like animal herding. Nonequilibrium processes inherently violate the detailed balance between the forward and reverse transitions, yielding time-asymmetric, irreversible dynamics.
Stochastic thermodynamics has clarified that this timeasymmetry is essential for systems to sustain their organized structure by dissipating entropy into the environment [6–9]. Further, the thermodynamic uncertainty
relation [10–13] and the thermodynamic speed-limit theorem [14, 15] show that dissipation sets fundamental
bounds on how precisely and rapidly systems can evolve.
Neural systems are no exception. In animals engaged
in behavioral and cognitive tasks, the dynamics of neuronal population activity exhibit hallmarks of nonequilibrium systems. Notable examples include the rotational activity of M1 neurons during motor execution
tasks [16, 17] and the sequential patterns observed in
hippocampal neurons, including their replay, during navigation and sleep [18–20]. Since the original proposal of
cell assembly and its phase sequences by Donald O. Hebb
[21], coordinated sequential patterns have been thought

∗ ishihara.ken.n7@elms.hokudai.ac.jp
† h.shimazaki@i.kyoto-u.ac.jp

fundamental for memory consolidation and retrieval [22–
25]. Recently, studies on fMRI or ECoG suggested that
increased time-asymmetry in neural signals, quantified
by steady-state entropy production [7, 26, 27], could serve
as a signature of consciousness [28–31] or reflect the cognitive load demanded by tasks [32]. For instance, entropy
production measured from ECoG signals of non-human
primates is diminished during sleep and certain types
of anesthesia compared to wakefulness [28, 31], indicating that the awake state includes more directed temporal patterns. However, assessing entropy production directly from neuronal spiking activities remains challenging. Further complicating this issue, neural signals exhibit nonstationary dynamics, including transient or oscillatory behavior, which hinders the use of steady-state
entropy production metrics.
The kinetic Ising model is a prototypical model of recurrent neural networks [33, 34]. It extends the equilibrium Ising model, which has been successfully applied
to empirical spiking data to elucidate the thermodynamic and associative-memory properties of neural systems [35, 36]. In the kinetic Ising system, neurons are
causally driven by the past states of self and other neurons, as well as a force representing the intrinsic excitability of the neurons and/or an influence of unobserved concurrent signals. When neurons receive steady inputs and
their causal couplings are asymmetric, the system does
not relax to an equilibrium state. Instead, it exhibits
steady-state nonequilibrium dynamics characterized by
non-zero entropy production. Recent theoretical studies
on steady-state entropy production have elucidated its
behavior in relation to distinct phases of the Ising system, including critical phase transitions [37]. Mean-field

2
theories have been developed for kinetic Ising systems
[38–43], enabling the estimation of steady-state entropy
production from large-scale spike sequences [43]. However, neuronal activity exhibits dynamical changes not
only in firing rates but also in the strength of their interactions, both of which violate the steady-state assumptions.
To account for the nonstationary dynamics of neural
systems, the state-space method [44, 45] has been applied to the Ising system [46–50]. In these approaches,
Bayesian filtering and smoothing algorithms have been
developed to estimate time-dependent parameters of the
Ising model, along with an EM algorithm [51, 52] to optimize various hyperparameters. These models have enabled researchers to trace time-varying neuronal interactions while neurons’ internal parameters change dynamically, absorbing the effect from unobserved concurrent
signals. Additionally, it has elucidated the thermodynamic quantities of neural systems (e.g., free energy and
specific heat) in a time-dependent manner, in relation
to the behavioral paradigms of tasks [48]. Nevertheless,
these methods assume an equilibrium Ising model with
symmetric couplings, which limits their ability to assess
the nonequilibrium properties of observed neural activities.
In this study, we develop the state-space kinetic Ising
model to account for the nonstationary and nonequilibrium properties of neural activities. We also construct
a mean-field method for estimating time-varying entropy
flow, an essential component of entropy production that
quantifies the dissipation of entropy, from spiking activities of neural ensembles. Given this method, we hypothesize that entropy flow, as estimated with the kinetic
Ising framework, reflects the capacity of neural populations to perform meaningful computation under energetic
and behavioral-time constraints [53]. Specifically, we expect that high-performing animals would exhibit greater
entropy flow per spike, consistent with efficient coding.
Application of the methods to mouse V1 neurons
revealed behavior-dependent changes in entropy flow.
From the analysis of 37 mice, we found that while spike
rates of the populations are lower on average and exhibited sparser distributions when mice actively engaged
in tasks than in the passive condition, active engagement
significantly enhanced the variability of the neuronal couplings, which contributed to increasing entropy flow. Further, higher-performing mice exhibited stronger entropy
flow per spike in active engagement than in the passive
condition. We corroborated contributions of couplings
to this tendency using trial-shuffled data that excluded
influences of firing rate dynamics and sampling errors in
estimating neuronal couplings. Thus, the method enabled us to reveal contributions of behavior-related neuronal couplings to the causal activities in sparsely active
neuronal populations, while isolating firing rate dynamics. These results imply economical representations of
stimuli by time-asymmetric causal activity in competent
mice.

This paper is organized as follows. In Results, we
first introduce the state-space kinetic Ising model and
its estimation method. Next, we introduce the meanfield method for estimating entropy flow. We validate
these methods through simulations and then apply them
to mouse V1 data. Finally, we relate our findings to previous studies and discuss their implications for efficient
information coding in neural populations.

RESULTS
The state-space kinetic Ising model

In neurophysiological experiments, the experimentalists simultaneously record the activity of multiple neurons while animals are exposed to a stimulus or perform
a task, and repeat the recordings multiple times under
the same experimental conditions. We analyze the quasisimultaneous activity of neurons using binarized spike
sequences. For this goal, we convert the simultaneous
sequences of spike timings of N neurons into sequences
of binary patterns by binning them with a bin width of
∆ [ms]. We assign a value of 1 if there is one or more
spikes in a bin and 0 otherwise. We assume that there
are T + 1 bins for each trial, with an initial bin being the
0-th bin and L trials in total. Below, we treat the bins
as discrete time steps and refer to the t-th bin as time t.
We let xli,t = {0, 1} be a binary variable of the i-th neuron at time t in the l-th trial (i = 1, . . . , N , t = 0, . . . , T ,
l = 1, . . . , L). We collectively denote the binary patterns
of simultaneously recorded neurons at time t in the l-th
trial using a vector, xlt = (xl1,t , . . . , xli,t , . . . , xlN,t ). Further, we denote the patterns at time t from all trials by
xt = (x1t , . . . , xlt , . . . , xL
t ) and denote all the patterns up
to time t by x0:t .
We construct the state-space kinetic Ising model to
account for the nonequilibrium dynamics of the binary
sequences by extending the state-space models developed
for equilibrium Ising systems [47, 48]. The state-space
model is composed of the observation model and the state
model. The observation model in the t-th bin is
p(xt |xt−1 , θ t ) =

L Y
N
Y

p(xli,t |xlt−1 , θ it )

l=1 i=1

=

L Y
N
Y
l=1 i=1


exp θi,t xli,t +

N
X


θij,t xli,t xlj,t−1 − ψ(θ it , xlt−1 ) ,

j=1

(1)
where θi,t is a time-dependent (external) field parameter
that determines the bias for inputs to the i-th neuron at
time t and θij,t is a time-dependent coupling parameter
from the j-th neuron to the i-th neuron. These parameters are collectively denoted as θ t = (θ 1t , . . . , θ it , . . . , θ N
t )
and θ it = (θi,t , θi1,t , . . . θij,t , . . . , θiN,t ). ψ(θ it , xlt−1 ) is the

3
log normalization term defined as


ψ(θ it , xlt−1 ) = log 1 + exp θi,t +

N
X


θij,t xlj,t−1  .

j=1

(2)
We also specify p(x0 ), a probability mass function of the
binary patterns at t = 0, which we assume p(x0 ) =
QN QL
l
l
i=1
l=1 p(xi,0 ), where p(xi,0 ) = 0.5 for data generation.
Next, we introduce a state model of the time-varying
parameters θ t for t = 1, . . . , T :
"
#
N
T
Y
Y
i
i i
i
i
i
p(θ 1:T |w) =
p(θ 1 |µ , Σ )
p(θ t |θ t−1 , Q ) , (3)
t=2

i=1

where w denotes the collection of the hyperparameters:
w = [µ1 , . . . , µN , Σ1 , . . . , ΣN , Q1 , . . . , QN ]. Namely, we
assume independence of the parameters of a neuron from
those of the other neurons, which significantly reduces
computational costs. The transition of the i-th neuron
follows the linear Gaussian models:
p(θ it |θ it−1 , Qi )



1 i
i
i
⊤
i −1 i
exp (θ t − θ t−1 ) (Q ) (θ t − θ t−1 ) ,
=p
2
|2πQi |
(4)
1

while the initial density p(θ i1 |µi , Σi ) is given by the Gausi
i
sian distribution with mean µ and covariance Σ .

Our goal is to obtain the approximation of the posterior density of the trajectory θ 1:T given the observed
neural activity x0:T :
(5)

while optimizing the hyperparameters w under the principle of maximizing marginal likelihood:
p(x0:T |w) = p(x0 )

T
Y

p(xt |x0:t−1 , w)

t=1

= p(x0 )

T Y
L Y
N Z
Y

Entropy flow

Using the inferred parameters θ 1:T of the kinetic Ising
model from spike data, we estimate entropy flow (also
known as bath entropy change) at each time step. The
entropy flow at time t is defined as:
X

σtflow =

p(xt , xt−1 ) log

xt ,xt−1

p(xt |xt−1 )
,
p(xt−1 |xt )

p(xli,t |xlt−1 , θ it )p(θ it |xl0:t−1 , w) dθ it .

(7)

where p(xt−1 |xt ) represents the probability of observing time-reversed processes generated under the forward
model. Because we use the natural logarithm, we report
entropy flow in units of nats. Eq. 7 is related to the
entropy production σt at time t as follows [7, 9, 26, 27]:
σt =

X

p(xt , xt−1 ) log

xt ,xt−1

p(xt |xt−1 )pt−1 (xt−1 )
p(xt−1 |xt )pt (xt )

= (St − St−1 ) + σtflow .

Model fitting and inference

p(x0:T |θ 1:T )p(θ 1:T |w)
p(θ 1:T |x0:T , w) =
,
p(x0:T |w)

while fixing the approximate posterior (M-step). The
construction of the approximate posterior density at the
E-step is performed by sequentially applying Bayes algorithms in a forward and backward manner, where we
approximate the posteriors by Gaussian distributions using Laplace’s method. Thus, the method yields the mean
and variance of the approximated Gaussian posterior at
time t, which are denoted as θ t|T and Wt|T , respectively.
See Methods and Supplementary Note 1 for the details
of the algorithm.

(8)

Here pt (xt ) is the marginal probability mass function of
the system at time t. St is the entropy of the system at
time t defined as
X
St = −
pt (xt ) log pt (xt ).
(9)
xt

The entropy production is non-negative: σt ≥ 0. Thus,
the positive entropy flow allows a decrease in the system’s entropy: namely, the system can be more structured or organized when the entropy flow is positive.
Since it is challenging to estimate the system’s entropy or
its change, here we estimate the entropy flow, which provides the lower bound of the entropy change: St −St−1 ≥
−σtflow .
Similarly, since the total entropy production across all
time steps σ1:T is given as

t=1 l=1 i=1

(6)
Here, p(θ it |xl0:t−1 , w) is the one-step prediction density.
The Expectation-Maximization (EM) algorithm [54]
offers a way to construct the approximate posterior with
optimized hyperparameters by alternately constructing
the approximate posterior density while fixing the hyperparameters (E-step) and optimizing the hyperparameters

σ1:T =

T
X
t=1

σt = (ST − S0 ) +

T
X

σtflow ,

(10)

t=1

PT
flow
the total entropy flow
provides the lower
t=1 σt
bound of the system’s entropy change from the initial
PT
and final time step: ST − S0 ≥ − t=1 σtflow . This indicates that the positive total entropy flow enables the

4
systems to be more structured (i.e., lower entropy) at the
final time step than at the initial time step.
In this study, we refer to Eq. 7 as entropy flow because
it is related to heat flow to reservoirs (thermal bath) and
the entropy change of the reservoirs in thermodynamics
[53]. We note that Eq. 7 differs from the entropy flow
defined in [55, 56], which was obtained by the decomposition of the dissipation function [27] as an alternative to
entropy production. See [27, 57] for their distinct definitions and decompositions for the case of discrete-time
systems.
For the case of the kinetic Ising model, the entropy
flow is written as
X

σtflow =
θi,t Ext xi,t − Ext−1 xi,t−1
i

+

X

θij,t Ext ,xt−1 (xi,t xj,t−1 − xi,t−1 xj,t )

i,j

−

X

is entropy of (0, 1) binary random variables with mean
r(h) = 1/(1 + e−h ):
χ(h) = −r(h)h + ψ(h),

where we redefined the log normalization function ψ as
a function of h: ψ(h) = log(1 + eh ). ϕi,t (h) is given by
ϕi,t (h) = −mi,t−1 h + ψ(h),

(16)

where mi,t−1 is the mean-field activation rate of i-th neuron at time t − 1 (see below for how
p to obtain it).
Here, the input h = gi,t,s + z ∆i,t,s is a Gaussian
random variable with mean gi,t,s and variance ∆i,t,s (s =
t, t−1), where z denotes a standardized Gaussian random
variable. gi,t,s and ∆i,t,s are computed using the meanfield activation rate at time s, mi,s , as
X
gi,t,s = θi,t +
θij,t mj,s ,
(17)
j


Ext−1 ψ(θ it , xt−1 ) − Ext ψ(θ it−1 , xt ) ,

∆i,t,s =

i

(11)
where Ext and Ext ,xt−1 represents expectation by p(xt )
and p(xt , xt−1 ), respectively.

(15)

X

2
θij,t
mj,s (1 − mj,s ).

(18)

j

The mean-field activation rate mi,t can be recursively
computed using
Z
p
mi,t ≈ Dz r(gi,t,t−1 + z ∆i,t,t−1 ),
(19)

Mean-field estimation of entropy flow

Entropy flow (Eq. 7) requires the expectation by the
joint density p(xt , xt−1 ), which is computationally expensive for large systems. While the mean-field methods for the kinetic Ising model [38–43] were employed
to estimate steady-state entropy flow [43], the mean-field
method for estimating time-varying entropy flow remains
unexplored. Here, we develop the mean-field method for
estimating dynamic entropy flow.
The entropy flow σtflow can be decomposed into the
forward and reverse components,
σtflow = −σtforward + σtbackward ,

(12)

where σtforward and σtbackward denote the conditional entropies of the forward and time-reversed conditional
distributions, respectively. The proposed mean-field
method estimates the entropy flow by approximating the
forward and time-reversed conditional entropies using the
Gaussian integral:
σtforward ≈

N Z
X

Dz χ(gi,t,t−1 + z

p

∆i,t,t−1 ),

(13)

∆i,t,t ),

(14)

i=1

σtbackward ≈

N Z
X

Dz ϕi,t (gi,t,t + z

p

starting with nominal values of mi,0 . In this study, we
use spiking probability averaged over all time bins and
trials for each neuron as mi,0 .
We also note that under the steady-state assumption,
the mean-field approximation can be expressed using the
stationary parameters mi , gi , and ∆i as (See Supplementary Note 3):

 p
XZ
p
σtflow ≈
Dz r(gi + z ∆i ) − mi · z ∆i . (20)
i

√ 
The term r gi + z ∆i − mi quantifies how the neuron’s activity
rate deviates from its long-term average,
√
while z ∆i represents the fluctuations of the input it
receives. The steady-state mean-field solution thus provides an intuitive view of entropy flow as a measure of
a neuron’s causal responsiveness to input fluctuations –
a quantity that captures the correlation underlying Hebbian plasticity in neural systems. However, this equation
also clarifies that the approximation depends mainly on
the magnitudes of the field and coupling parameters and
is thus insensitive to the detailed coupling structure. It
should therefore be applied with caution when the degree
of coupling asymmetry is the primary determinant of the
strength of entropy flow.

i=1

Simulation: Estimating the model parameters


where Dz = √dz
exp − 12 z 2 . See Methods and Supple2π
mentary Note 2 for the derivation of these results. The
functions χ(h) and ϕi,t (h) are given as follows. χ(h)

We begin by testing the proposed method by estimating the time-dependent parameters of a kinetic Ising

5

E

A

Neuron 1

Neuron 2

B

C
D

FIG. 1.
Application of the state-space kinetic Ising model to two simulated neurons. A A schematic of the
time-dependent kinetic Ising model for two neurons with field and coupling parameters. The links between the nodes represent
the neurons’ causal interactions with arrows indicating the time evolution from the past to the present. B Raster plots
for the two neurons. The vertical axis represents the number of trials, and the horizontal axis shows the number of time
bins. C The approximate marginal log-likelihood as a function of the iteration steps of the EM algorithm. D The optimized
hyperparameter Qi for neuron 1 (left) and neuron 2 (right). E (top) Estimated and true time-dependent field parameters.
The solid lines represent the MAP estimates of the field (first-order) parameters obtained from the smoothing posterior, θ t|T .
The shaded areas show the 95% credible intervals derived from the diagonal elements of the smoothed covariance matrix,
Wt|T . The dotted lines are the field parameters from true θ t used to generate the data. (middle, bottom) Estimated and true
time-dependent coupling (second-order) parameters.

model consisting of two simulated neurons (Fig. 1A). Figure 1B shows the spike data generated using Eq. 1 with
the number of bins, T = 400, and the number of trials,
L = 200. The time-dependent parameters θ 1:T used to
generate binary data were sampled from Gaussian processes (See Methods).
The EM algorithm was applied to this spike data until
the log marginal likelihood converged (Fig. 1C). Figure
1D shows the components of the optimized hyperparameter matrices, Qi (i = 1, 2). Figures 1E show the MAP
estimates of the time-dependent fields θi,t and couplings
θij,t under the optimized hyperparameters (solid lines)
with 95% credible intervals (shaded areas). The results
confirm that the method uncovers the underlying timedependent parameters (black dashed lines) used to generate the data.
Next, we applied the state-space kinetic Ising model

to a network of 12 simulated neurons to estimate the
time-varying field and coupling parameters between neurons. Figure 2A presents the spike data generated using the observation model with the number of bins set
to T = 75 and the number of trials L = 200. Data
generation and model estimation procedures follow the
two-neuron case above. Figure 2B shows the estimated
time-varying coupling parameters θij,t for each neuron.
In Fig. 2C, we compare the estimated coupling parameters θ t|T with the true values θ t at representative time
points (t = 10, 20, . . . , 60). The scatter plot shows agreement between the true and estimated values, with most
points aligning closely along the diagonal line, indicating that the model captured the underlying dynamics of
the coupling parameters. These results confirm that the
proposed state-space kinetic Ising model can reliably estimate time-varying coupling parameters in a network of

6
A

B

C

FIG. 2. The application of the state-space kinetic Ising model to 12 simulated neurons. A Simulated spike data
for the first, 100th, and last trial out of 200 trials. The vertical axis shows the number of neurons, and the horizontal axis
represents the number of bins. B Estimated coupling parameters θ t|T (solid lines), for all neurons and time bins (i = 1, 2, . . . , 12,
t = 1, . . . , T ). Shaded areas indicate 95% credible intervals, and dashed lines denote the true parameter values used to generate
the data. These plots show only the couplings that are significantly deviated from zero: The couplings whose 95% credible
interval contains 0 in all bins were excluded. For clarity, only five such significant incoming couplings from other neurons
are shown in each panel. C Scatter plots comparing the true coupling parameters θ t with the estimated values θ t|T at time
t = 10, 20, . . . , 60. The black line is a diagonal line.

simulated neurons.

Simulation: Estimation error and computational
time

We evaluated the performance of the proposed statespace kinetic Ising model in terms of estimation accuracy
and computational time, varying dataset and population
sizes (See Methods for parameter generation).
Estimation error: To assess estimation error, we computed the root mean squared error (RMSE) between the
true parameters θ t and the estimated parameters θ t|T
for both field and coupling parameters. Namely, RMSEs were computed separately for the field parameter
θi,t and the coupling parameter θij,t , then averaged over

time bins. The means over 10 independent samplings are
shown in Figures 3A and B with the standard deviations
represented by error bars.
For a fixed number of neurons (N = 80), RMSEs for
both field and coupling parameters decreased as the number of trials L increased (Fig. 3A), demonstrating improved estimation accuracy with more data. Conversely,
when the number of trials was fixed at L = 550, RMSEs
exhibited different trends depending on the parameter
type. The RMSE for the field parameter increased with
N , imposing the challenges of estimating field parameters in larger networks with limited data. The RMSE
for coupling parameters remained stable across different
neuron numbers in this simulation (Fig. 3B).
Computational time: We analyzed the computation
time for model fitting. Figure 3C illustrates the compu-

7
A

N=80 fixed: Field & Coupling error vs Number of trials

C

RMSE

Average computation time

Number of trials, L
R=550 fixed: Field & Coupling error vs Number of neurons

RMSE

B

Time (min)

L
L
L
L

Number of neurons, N

Number of neurons, N

FIG. 3. Estimation error and computational time. A Root mean squared error (RMSE) of the field and coupling
parameter estimation as a function of trials L, with the number of neurons fixed at N = 80. Results are averaged over 10
independent samples, with error bars representing standard deviations. B RMSE of the field and coupling parameters as a
function of the number of neurons N , with the number of trials fixed at L = 550. Averages and standard deviations are computed
over 10 independent samples. C Average computation time for different numbers of neurons N and trials L = 55, 100, 300, 550,
with error bars indicating standard deviations. Computation was performed on a Dell PowerEdge R750 server with two Intel
Xeon 2.4 GHz CPUs (76 cores / 152 threads).

tation time required to complete the EM algorithm for
different numbers of neurons N and trials L. The results
indicate that estimation with N = 80 and L = 550 trials
can be completed in approximately one hour, making it
feasible for practical data analysis. Nevertheless, computation time scales with both N and L, highlighting the
necessity for further optimization to enable large-scale
analysis. The assumption of independent state evolution
for individual neurons (Eq. 3) significantly reduces computational complexity by enabling independent calculations for filtering, smoothing, and parameter optimization per neuron, which can be further accelerated through
parallel updates. Another potential improvement is replacing the current filtering method, which employs exact
Newton-Raphson optimization for maximum a posteriori
(MAP) estimation, with quasi-Newton or mean-field approximations, as demonstrated in equilibrium state-space
Ising models [48].

Simulation: Estimating entropy flow

In this section, we assess the proposed mean-field approximation method for estimating entropy flow. As in
the previous section, we generated spike samples from

time-dependent parameters θ 1:T sampled from Gaussian
processes. All simulations were conducted with N = 80,
T = 75, and L = 550 trials. We then estimated the
time-dependent field and coupling parameters from the
data. Using the posterior mean θ t|T , we obtained the
mean-field approximation of the time-dependent entropy
flow (Eq. 12, using Eqs. 13 and 14). The solid red line
in Fig. 4 represents the entropy flow calculated using the
mean-field approximation with the learned parameters.
To verify the consistency of the estimated entropy flow,
we calculated the entropy flow using a sampling-based
method to compute the expectation over the two-step
trajectories (solid black). This approach involves repeatedly running the kinetic Ising model (Eq. 1) using the
true parameters to sample binary spike sequences. This
process was performed ns = 10, 000 times to empirically
estimate the joint distribution p(xt , xt−1 ). Using this
empirical distribution, we obtained a sample estimate of
the entropy flow as follows:

ns
p xst |xst−1
1 X
flow
,
σ̂t =
(21)
log
ns s=1
p xst−1 |xst
where xst denotes the s-th sample at time t. This sampling estimation using the true parameters serves as the
baseline.

8

20

Entropy flow

15

10

5

0
20

40

60

80

100

120

140

Time

FIG. 4. Comparison of entropy flow estimation methods. Entropy flows estimated using four different approaches:
Sampling method with true parameters θ t (solid black); sampling method with estimated parameters θ t|T (dashed green);
mean-field method with true parameters θ t (dashed blue);
and mean-field method with estimated parameters θ t|T (solid
red).

The mean-field estimation of the entropy flow (solid
red) follows the trajectory of the baseline sampling estimation using the true parameters (solid black). The result confirms that the proposed method is applicable for
entropy flow analysis while ensuring computational feasibility. The slight discrepancy between the two lines is due
to the errors in estimating the time-dependent parameters and/or the mean-field approximation (in addition to
sampling fluctuation inherent to the sampling method).
To separate these effects, we estimated the entropy flow
by the mean-field approximation using the true parameters θ 1:T used for the data generation (dashed blue).
This estimation deviated from the baseline sampling estimation. In contrast, the sampling method using estimated parameters (dashed green) did not significantly
differ from the baseline. Thus, the discrepancy arose
from the mean-field approximation, rather than from inaccuracies in parameter estimation. These results suggest that refining the mean-field method could further
improve the accuracy of entropy flow estimation.

Simulation: Model limitations

We end the simulation analysis by acknowledging that
assumptions of the kinetic Ising framework, in particular
pairwise couplings and conditional independence, represent simplifications that may not faithfully capture neural population dynamics. To demonstrate this, we fitted the kinetic Ising model to population activity, using a neuronal population model called the alternatingshrinking higher-order interaction model, which accounts
for deviations from the logistic activation function of individual neurons and exhibits higher-order interactions
[58].
In this model, homogeneous binary population activity
was generated using an exponential-family distribution
with interactions of all orders (Eq. 63 in Methods). The
model was designed so that the spike-count histogram

of the population exhibits sparse yet widespread characteristics (Fig. 5A, green), consistent with empirical
data. We performed Gibbs sampling from this distribution (blue circle), which corresponds to the dynamics of
recurrent networks with an extended activation function
(See Methods).
When the state-space kinetic Ising model was fitted
to these activities, it failed to reproduce the observed
spike-count histogram (Fig. 5A, yellow). One reason is
its restriction to pairwise interactions, which prevents
it from capturing higher-order dependencies. Reproducing widespread spike-count histograms in large populations is known to require interactions of all orders
[59]. By contrast, the pairwise model concentrates probability mass on only up to two points in the limit of
large N , often overestimating the tail because it neglects the higher-order interactions that generate sparse,
heavy-tailed distributions. The mismatch in model architectures is also apparent in their activation functions
(Fig.5B). The alternating-shrinking higher-order interaction model exhibits a supra-linear activation function due
to the nonlinear integration of synaptic inputs (Eq. 71 in
Methods). In contrast, the kinetic Ising model employs
the classical logistic activation function with a linear sum
of synaptic inputs (Eq. 1).
In addition, an equally profound architectural limitation lies in the assumption of conditional independence, which enforces synchronous updates across neurons within each step. Gibbs sampling, by contrast, uses
sequential (or randomly ordered) updates that guarantee detailed balance and allow neurons to incorporate
the most recent changes, enabling activity to propagate
within a sweep and generate synchronous states. Because
the kinetic Ising model updates all neurons simultaneously from the previous state, it lacks this recruitment
mechanism and consequently fails to drive synchronous
activity appropriately.
The results highlight that caution is warranted in applying the kinetic Ising framework: although it offers a
tractable statistical description, its simplifying assumptions constrain the neural dynamics it can represent. In
particular, entropy flow estimates should be regarded as
quantities defined under the pairwise and synchronousupdate assumptions.

Mouse V1 neurons: Experimental design and data
description

Having confirmed the applicability of our methods using simulation data, we next applied the state-space kinetic Ising model to empirical data obtained from mice
exposed to visual stimuli and estimated its entropy flow.
In this study, we analyzed the Allen Brain Observatory: Visual Behavior Neuropixels dataset provided by
the Allen Institute for Brain Science, which contains
large-scale recordings of neural spiking activity of mouse
brains during the visual change detection task (See [60–

9
Population count histogram

A

Theoretical (shifted geometric distribution)
Gibbs sampler
kinetic Ising model (fitted)

10-1

Activation function

B

Alternating-shrinking model
kinetic Ising model (fitted)

1.0

10-2
p(x_i=1 | n)

Probability density (log scale)

0.8

10-3

0.6

0.4

10-4
0.2

10-5
0.0
0

5

10
15
20
Number of active neurons

25

30

0

5

10
15
20
Number of active input units, n

25

30

FIG. 5. Analysis of the model misspecification. A The population spike count histogram of N = 30 neurons following
the shifted-geometric model with a sparseness parameter f = 20 and τ = 0.8 (empirical distribution obtained by the Gibbs
sampling in blue circle; theoretical probabilities in green). The yellow line represents a distribution obtained from the statespace kinetic Ising model fitted to the Gibbs sampling data. B The activation function of the shifted-geometric model with
f = 20 and τ = 0.8 (green) and that of the kinetic Ising model (yellow) using the average of the fitted field and coupling
parameters.

62] for analyses using this data set). The task is designed
to analyze the effect of novelty and familiarity of the stimulus on neural responses. One of two image sets (G and
H) was presented to animals at the training/habituation
and recording sessions with different orders. The G and
H image sets contain 8 natural images. We analyzed the
recordings of 37 mice available from the Allen dataset,
which were exposed to stimulus G in the recording sessions (either day 1 or 2) whereas the same stimulus G was
used in the training and habituation sessions prior to the
recording sessions (i.e., the case in which G is familiar).
The neural activities were recorded under two distinct
conditions, in which the mice were either actively or passively performing the task under the same set of images. The active condition involved the mice performing a go/no-go change detection task, where they earned
a water reward upon detection of a change in the visual stimulus, measured by licking behavior. Each of
the 8 stimuli was presented for 250 ms, followed by a
500 ms interstimulus interval (gray screen), repeating for
one hour while mice actively engaged in the task for reward. In contrast, the passive condition involved replaying the same visual stimuli used in the active condition
but without providing any rewards or access to the lick
port. In this study, we analyzed recordings with images
labeled im036 r, im012 r, and im115 r, which are used in
the training session and classified as Familiar, and compared neural responses under the active and passive conditions. We used all presentations of the images equally
and treated one presentation as a trial.
We selected neurons in the V1 area for analysis. For
each mouse, we analyzed the simultaneous activity of
neurons during a 750-ms period following the image on-

set. Although the number of trials varies across mice,
the mean trial count was 566 with 356 and 652 as the
minimum and maximum number of trials, respectively,
for the case of an image im036 r.

Mouse V1 neurons: An exemplary result from a
single mouse

We constructed binary sequences using a 10 ms bin,
which resulted in T = 75 time bins. Here, we focused
on the analysis of im036 r. Figure 6A (Left) shows the
spike-rate averaged over neurons at each time under the
active and passive conditions (population-average spike
rate) from an exemplary mouse (574078). The overall
temporal profiles were similar across the active and passive conditions. In both conditions, the population exhibited higher mean spike rates during the stimulus presentation period (0-250 ms) than the post-stimulus period (250-750 ms). However, their magnitudes significantly differed across the conditions. The passive condition (blue) showed consistently higher spiking probabilities than the active condition (red) throughout the stimulus and post-stimulus periods. In agreement with the
population-average spike-rate dynamics, time-averaged
spike rates of individual neurons exhibited a sparser distribution during the active condition compared to the
passive condition (Fig. 6A Right).
We then applied the state-space kinetic Ising model to
the binary activities of these neurons. For this goal, we
selected the top N = 80 neurons with the highest spike
rates. The estimated dynamics of the field and coupling
parameters exhibited variations in both active and pas-

10

A

B

C

FIG. 6. Estimated neural dynamics under the active and passive conditions for mouse 574078. A Spike-rate
dynamics and distributions. (Left) Spike-rate averaged across neurons and trials. (Right) Spike-rate distributions of all
recorded neurons. B Smoothed time-dependent parameters θ t|T of the kinetic Ising model for the active (top) and passive
(bottom) conditions. The first column shows the field θi,t (one trace per neuron), and the next three columns show the
incoming couplings θij,t for i = 1, 2, 80. Solid lines are MAP estimates and shaded areas indicate ±1 SD (i.e., 68% credible
bands) computed from the diagonal of the posterior covariance. For each i, couplings were first screened within the analysis
window (bins 21-75) and retained if their credible interval excluded zero at least once in the window (self-couplings excluded).
From the retained set, we display the first five couplings per i, ordered by ascending j label for readability. C Estimated
couplings at t = 5, 25, 35, 50 under the active (top) and passive (bottom) conditions.

11
sive conditions (Fig. 6B). Notably, the field parameters
θi,t (the first column) follow the dynamics of the mean
spike rate of the population with significant fluctuations.
On the contrary, the dynamics of the coupling parameters θij,t exhibited smoother transitions. To clarify the
dynamics of the couplings, we show them in the matrix
form at specific time points, t = 5, 25, 35, 50 (Fig. 6C).
The neurons are indexed in the ascending order of the
average firing rates. The top and bottom rows show the
results of the active and passive conditions, respectively.
Coupling strength is indicated by graded color, with red
and blue representing positive and negative values, respectively. The results show that (i) the couplings exhibit
significant variations with positive and negative values;
(ii) the variations are stronger in the active condition
than in the passive condition; (iii) the diagonal components of the couplings (self-correlations) mostly display
negative correlations.
To corroborate the above observations, we performed
the same analysis on the trial-shuffled data (Supplementary Fig. S1). The analysis of trial-shuffled data reveals
bias and variance in estimation under the assumption of
neuronal independence. The result shows a significant reduction in the magnitude and variability of the couplings,
whereas self-couplings remained unchanged (note that
the self-coupling remains after trial-shuffling). However,
non-zero couplings persisted with stronger variations in
the active condition than in the passive condition, reflecting sampling fluctuations due to the lower firing rates in
the active condition. These findings indicate that the parameters observed in Fig.6B,C include estimation noise,
necessitating statistical analyses to confirm their significance.

Mouse V1 neurons: Population analysis across mice

We assessed key features identified in the exemplary
mouse (Fig. 6) across all mice by comparing them with
trial-shuffled data.
First, the firing rate profiles with reduced activity in
the active conditions found in Fig. 6A were consistently
observed across all mice with a few exceptions (Supplementary Fig. S2 and S3). We compared the mean and
sparsity of the firing rate distributions of individual neurons between the two conditions across all 37 mice (Supplementary Fig. S4). Sparsity of a non-negative firing
rate distribution was quantified by the coefficient of variation (CV) [63]. The V1 neurons exhibited diminished
and sparser firing rate distributions in the active condition than in the passive condition, as confirmed by the
reduced mean spike rates (p = 1.556 × 10−8 , Wilcoxon
signed-rank test) and increased CVs (p = 8.35 × 10−8 ,
Wilcoxon signed-rank test).
Next, we assessed key statistical features of the estimated parameters of the state-space kinetic Ising model.
Figure 7A-C illustrates these features for an exemplary
mouse (574078). Figure 7A, B shows distributions of

time-averaged fields θi,t and couplings θij,t under the active and passive conditions, while Figure 7C shows a
scatter plot of time-averaged reciprocal couplings θij,t vs
θji,t to evaluate coupling asymmetry. In the active condition, the medians of field parameters decreased, reflecting
reduced firing rates, while the medians of couplings remained near zero in both conditions. Field and coupling
parameter variances increased, and coupling asymmetry
strengthened in the active condition. These trends were
consistent across all mice (Fig. 7D-F). These characteristics represent key aspects of neural dynamics that are
closely related to entropy flow, although they are not entirely independent of each other.
While increased parameter variabilities and coupling
asymmetry were observed under the active condition,
they may be influenced by the lower neuronal activity. To examine this, we compared results with trialshuffled data across all mice. Figures 7G-I show field
and coupling variances in both conditions, adjusted by
subtracting shuffled data values for each mouse. Notably, observed values in both active and passive conditions were significantly higher than shuffled data: p =
2.91×10−11 (active), p = 1.103×10−7 (passive) for fields,
p = 4.676 × 10−8 (active), p = 1.455 × 10−11 (passive) for
couplings (Wilcoxon signed-rank test). Note that the observed significant heterogeneity in the field parameters is
likely associated with the coupling heterogeneity. These
results confirm that the variability observed in active or
passive conditions is not explained by noise couplings.
The coupling asymmetry was higher than shuffled results
only for the active condition (p = 1.185 × 10−5 (active)
and p = 0.1287 (passive) for asymmetry).
Comparisons of these significant changes of the parameter variability (i.e., shuffled results subtracted) between
the active and passive conditions showed significantly
greater values in the active condition (p = 8.273 × 10−4
for fields, p = 6.421 × 10−4 for couplings, Wilcoxon
signed-rank test, Fig.7G,H), indicating greater variabilities in both field and coupling parameters during active
behavior. A similar analysis of the mean couplings across
mice revealed slightly but significantly larger values under the active condition (Supplementary Fig. S5). In
contrast, coupling asymmetry showed no significant difference (p = 0.1287, Wilcoxon signed-rank test, Fig.7I).
The lack of statistically discernible change in asymmetry in the effective couplings accords with the use of the
proposed mean-field method for comparing the coupling
effect, which primarily arises from variability change.
These findings validate enhanced parameter variability in
the sparse neuronal activity during active engagement.

Mouse V1 neurons: Entropy flow dynamics

Using the estimated parameters of the state-space kinetic Ising model, we computed entropy flow dynamics.
Figure 8A shows the time-varying entropy flow of a representative mouse (574078) under the active and passive

12
A

B

C

D

E

F

G

H

I

FIG. 7. Variability of estimated model parameters. A, B Distributions of the time-averaged field values θ̄i (A) and
the time-averaged couplings θ̄ij (B) for mouse 574078 under the active and passive conditions. The shaded violin plots depict
kernel-density estimates of the empirical distributions; gray dots are the underlying observations (one dot per neuron in A, one
per coupling in B). Short horizontal caps at the top and bottom indicate the sample maximum and minimum, respectively.
Horizontal red bars mark the mean, while horizontal green bars mark the median. C: Scatter plots of coupling strength
of reciprocal pairs under the active (red) and passive (blue) conditions for mouse 574078. The coupling asymmetries were
0.147 (active) and 0.105 (passive). The asymmetry was assessed by the average absolute difference of the reciprocal couplings
⟨|θ̄ij − θ̄ji |⟩ij , where θ̄ij indicates the time-average of θij,t and ⟨·⟩ij refers to the average over the combinations of i, j. D-F
Group-level (all mice) comparisons for the original dataset: field variance (D), coupling variance (E), and coupling asymmetry
(F). G-I: Plots analogous to D-F for shuffle-subtracted parameter variances and coupling asymmetry. Each subplot of D-I
contains the p-values of Wilcoxon signed-rank tests for the active vs. passive conditions.

conditions (red and blue solid lines, respectively). In
both cases, transient increases in entropy flow coincided
with declines in the mean population spike rate (dashed
lines). Similar patterns appeared across all mice analyzed
(Supplementary Fig. S6). These increases align with the
second law, indicating that greater entropy dissipation
is required when the system is transitioning to a lower
entropy state, characterized by reduced firing rates.
The entropy flow time courses for this mouse showed
no clear differences between the active and passive conditions. To assess population-level effects, we analyzed
all 37 mice and computed total entropy flow across time

bins for each condition (Fig. 8B). The comparison revealed significantly lower total entropy flow in the active condition (p = 0.01159, Wilcoxon signed-rank test).
Note that neurons exhibited reduced firing rates (Supplementary Fig. S3) and increased parameter variability
(Fig. 7D,E) during the active condition.
To isolate the effect of couplings, we compared the
observed total entropy flows with shuffled data results
(Fig.8C). The estimated entropy flow for shuffled data
includes the impact of firing rate dynamics and estimation error on couplings from other neurons; therefore, subtracting shuffling results from observed entropy

13
A
14
12
10
8
6
4
2
0
0

10

20

30

B

40

50

60

70

C

FIG. 8. Estimated entropy flow dynamics. A Time courses of entropy flow for the original (solid lines) and shuffled data
(dash-dot lines) under the active (red) and passive (blue) conditions. The dashed lines show the corresponding populationaveraged spike rates. B Total entropy flows summed across all time bins for each mouse under active and passive conditions.
Data from the same mouse are connected by a line. C Shuffle-subtracted total entropy flow (original - shuffle), shown for each
mouse under the active and passive conditions.

flow isolates contributions of couplings among different
neurons beyond the sampling fluctuation. Positive values of the shuffle-subtracted total entropy flow in both
conditions indicate that the couplings caused a significant entropy flow increase (p = 1.455 × 10−11 for active, p = 1.455 × 10−11 for passive, Wilcoxon signedrank test). These shuffle-subtracted entropy flows behave in agreement with the theoretical prediction by the
Sherrington-Kirkpatrick model [37]. In the active condition, the increased coupling variability (and asymmetry)
from the shuffle-subtracted values were positively correlated with the shuffle-subtracted entropy flows, while the
increased field heterogeneity was negatively correlated
(Supplementary Fig. S7A-C). These effects disappeared
in the passive condition, possibly due to small changes in
the variabilities and asymmetry introduced by shuffling
(Supplementary Fig. S7D-F).

We analyzed the differences in coupling-related entropy
flows between the active and passive conditions for all
mice (Fig.8C). The result shows no significant difference between the two conditions (p = 0.1448, Wilcoxon
signed-rank test). However, coupling-related entropy
flows of indistinguishable magnitude emerged under distinct neural activity states: sparser, lower activity with
increased variability in field and coupling parameters in
the active condition; and less sparse, higher activity with
reduced variability in the passive condition. Thus, coupled with the previous results, this result indicates that
the greater coupling variability in the active condition
led to increased total entropy flow, making it comparable to the passive condition despite significantly sparser
firing rate distributions. Consistent with this view, a
recent study by Aguilera et al. using this dataset complementarily reported that a lower bound on entropy pro-

14
duction, derived under steady-state assumptions using a
variational framework, was higher in the active condition
when normalized per spike [13].

Mouse V1 neurons: Model-based perturbation
analysis

To further elucidate the difference in the estimated entropy flow in active and passive conditions, we performed
a model-based perturbation analysis by rescaling the fitted model parameters as θ → βθ and computing the
resulting entropy flow to assess its sensitivity to parameter perturbation. An example result from mouse 574078
(Fig.9A) shows that the entropy flows during stimulus
presentation and waiting (gray image) periods exhibited
distinct behaviors in response to the rescaling. The transient increases in entropy flow caused by firing rate reduction after stimulus onset and offset persisted as the
scaling parameter β increased. In contrast, we observed
that the entropy flow peaked at β < 1 during the waiting
period, where the neural activity is relatively stationary.
Both forward and reverse conditional entropies
(σtforward and σtbackward in Eq. 12) decreased with increasing β during the waiting period (Fig.9B,C), indicating
that both processes became more deterministic. This
trend suggests that, as β increases, the system transitions
from a disordered phase toward a ferromagnetic phase,
rather than into a quasi-chaotic regime [43]. Thus, these
results indicate that the subsampled neural population
during this period operates in a subcritical regime.
By subtracting the entropy flow estimated from trialshuffled data, which preserves only firing rate dynamics, we confirmed that the two bands of increased entropy flow associated with stimulus presentation are attributable to firing rate changes, whereas the increase at
β < 1 arises from interactions, since the former disappeared but the latter persisted after shuffle subtraction
(Fig.9D). The interaction-driven entropy flow revealed
by parameter scaling was stronger during the active condition than the passive condition (Fig.9D,E), a result
confirmed across all mice (Fig.9F). Notably, the previous analysis at β = 1 showed no difference in shufflesubtracted (i.e., interaction-driven) entropy flow between
the two conditions (Fig.8C). Thus, the model-based perturbation analysis uncovered differences in entropy flow
between active and passive states that were not apparent
at β = 1.

Mouse V1 neurons: Entropy flow and behavioral
performance

Finally, we investigated the relationship between neural dynamics and behavioral performance across individual mice. We quantified task performance by the sensitivity index d′ (mean d-prime) defined as the difference between the z-transformed hit and false-alarm rates

(Supplementary Note 4). In the following analyses, we
extended the analysis to include two additional images
(im012 r and im115 r).
First, we examined how sparseness, assessed from individual neurons’ activity rates, relates to behavioral outcomes. As shown in Supplementary Fig. S3, neuronal
activities were significantly reduced under active conditions, accompanied by increased sparsity of firing rate
distributions. To further characterize this effect, we examined whether the reduction was uniform across neurons or driven by a subset of neurons by computing the
skewness of the firing rate difference between active and
passive conditions (Fig. 10A). A uniform reduction results in a skewness of zero, whereas negative skewness
indicates that only some neurons decreased their activity,
reflecting the sparsification. We found that this sparsification index was significantly correlated with behavioral
performance measured by the d-prime, indicating that
task engagement is reflected in changes in sparsity quantified at the level of individual neurons’ activity rates
(Fig. 10B).
Having established the link between activity-rate sparsity and behavior, we next turned to entropy flow to ask
whether it provides additional explanatory power beyond
rate changes alone. The variability of effective couplings
was significantly higher during the active condition. To
gain insight into the contributions of couplings to entropy flow, we computed the activity rate and mean-field
entropy flow of individual neurons as a function of the
mean and variability of their inputs (Fig. 10C,D). Theoretically, in the low-input and stationary regime, entropy
flow increases with both higher mean input and greater
variability (Eq. 20, background color in Fig. 10D). We
observed that neurons receiving high mean input tended
to have less variable inputs, whereas neurons with low
mean input exhibited larger variability (colored circles).
These results suggest that total entropy flow is shaped
not only by high-input (typically high-firing) neurons but
also by low-input neurons with high variability.
These patterns imply two sources of entropy flow: (i)
mean-input-driven contributions that track high firing,
and (ii) variability-driven contributions that can be substantial even at low firing. To focus more on the latter,
we considered entropy flow per activity rate. This normalization reduces the direct dependence on mean rate
and makes variability-driven effects, particularly those
arising in low-rate neurons, observable on equal footing
with high-rate effects. The shift in mean entropy flow per
activity rate across individual neurons (active - passive)
was significantly correlated with behavioral performance
(Fig. 10E). Moreover, this correlation was weaker and
non-significant for trial-shuffled data, indicating contributions from highly variable couplings during active conditions (Fig. 10F). This finding suggests that the thermodynamic cost per spiking activity is related to mouse
performance, with couplings contributing in addition to
activity-rate sparsity.
As an alternative explanation, behavioral performance

15
A

B

Time

D

C

Time

E

Time

Time

F

Time

FIG. 9. Model-based perturbation analysis A Entropy flow σtflow of mouse 574078 in the active condition, computed after
rescaling the fitted parameters as θ → βθ. The dashed line indicates β = 1. B Forward entropy flow, σtforward . C Backward
entropy flow, σtbackward . D Shuffle-subtracted entropy flow in the active condition, isolating the contribution of interactions
beyond firing rate dynamics. Entropy flow driven by interactions peaks at β < 1. E Shuffle-subtracted entropy flow in the
passive condition. F Comparison of shuffle-subtracted entropy flow between active and passive conditions across all mice,
showing significantly higher values in the active condition (Wilcoxon test, p = 1.455 × 10−10 ). Shuffle-subtracted entropy flow
is obtained over a low-gain range β ∈ [0.2, 1.0] and across all bins. Lines connect active (left) to passive (right) for each mouse.

could be related to entropy-flow changes concentrated in
high-firing neurons. We therefore tested whether neurons
with higher spike rates tended to increase entropy flow
during active engagement in mice with higher task performance (Supplementary Note 5, Supplementary Fig. S8).
While this tendency correlated significantly with behavioral performance for one image, it was not significant for
the other two images. We therefore infer that high-firingbased changes alone cannot consistently account for performance differences. Instead, the more robust association with entropy flow per activity rate supports a complementary role of variability-driven, coupling-mediated
contributions – including those from low-rate neurons –
in explaining behavioral performance.
DISCUSSION

This study presents a state-space kinetic Ising model
for estimating nonstationary and nonequilibrium neural
dynamics and introduces a mean-field method for entropy flow estimation. Through analysis of mouse V1
neurons, we identified distinct field and coupling distributions across behavioral conditions. These structural
shifts influenced entropy flow compositions in V1 neurons, revealing correlations with behavioral performance.
To our knowledge, no inference methods have been
proposed for time-dependent kinetic Ising models within

the sequential Bayesian framework, which estimates parameters with uncertainty using optimized smoothness
hyperparameters (see [64] for a Bayesian approach in a
stationary case). While parameter estimation has often
been considered under time-dependent fields with fixed
couplings [40, 42] (see also [65, 66] for the equilibrium
case), exceptions exist [41] that provide point estimates
for time-varying couplings. These methods rely on meanfield equations relating equal-time and delayed correlations to coupling parameters, but estimating correlations
at each time step is often infeasible in neuroscience data
due to limited trial numbers in animal studies. Campajola et al. [67] proposed a point estimate of time-varying
couplings using a score-driven method under the maximum likelihood principle, but assumed all fields and couplings were uniformly scaled by a single time-varying parameter. In contrast, our state-space framework accommodates heterogeneous parameter dynamics and employs
sequential Bayesian estimation with optimized smoothness parameters. These innovations are crucial for uncovering parameter variability’s impact on causal population dynamics and elucidating individual neurons’ contributions.
Lower spike rates of V1 neurons observed during the
active condition (see also [60]) contrast starkly with previous reports showing increased firing rates during active task engagement [68] or locomotion [69, 70]. Nevertheless, the diminished spike-rates found in the active

16
B

Number of neurons

Behavioral performance (d’)

A

Skewness of activity rate difference distribution

Activity rate difference (Active - Passive)

C

D

E

F

Behavioral performance (d’)

Behavioral performance (d’)

FIG. 10. Correlations between neural dynamics and behavioral performance. A A histogram of firing rate differences
(active-passive) across neurons for mouse 574078 with an image im036 r. A skewness was used as a sparsification index. B The
skewness vs behavioral performance (mean d-prime) for 37 mice with three images. C Mean-field rates of individual neurons
(colored circles) as a function of time-average mean gi and variability ∆i of their inputs for mouse 574078. The background
color indicates the theoretical mean-field rate under the steady-state (Eq. 19). D Mean-field entropy flow of individual neurons
(colored circles) as a function of time-average mean and variability of their inputs (mouse 574078). The background color shows
theoretical entropy flow under the steady-state (Eq. 20). E Entropy flow difference (active - passive) normalized by activity
rate vs behavioral performance for 37 mice with three images. F Entropy flow difference normalized by activity rate obtained
from trial-shuffled data vs behavioral performance. In E and F, there is one outlier mouse below −20 in the ordinate, which
was included in the statistical analysis.

condition (Fig. 6A and Supplementary Fig. S1, S2) are

in agreement with sparse population activity in process-

17
ing natural images in mouse V1 neurons [71, 72]. Further, active engagement broadened distributions of field
and coupling parameters, possibly reflecting stronger and
more diverse inputs from hidden neurons [73, 74]. These
findings align with previously reported increased heterogeneous activities during the active condition and their
correlation to behavioral performance [75]. The observed
shift in cortical activity largely aligns with the effects of
neuromodulators, such as acetylcholine (ACh) [76, 77]
and norepinephrine (NE) [78], that alter local circuit
interactions and global activity patterns, thereby regulating transitions such as quiet-active, and inattentiveattentive states [79, 80]. For example, Runfeldt et al. [76]
demonstrated that spontaneous network events became
sparser under ACh, as the probability of individual neurons participating in circuit activity was markedly reduced. In addition, ACh altered the temporal recruitment of neurons, delaying their activation relative to
thalamic input and prolonging the window during which
stereotyped activity propagated through local circuits.
These findings indicate that ACh reorganizes cortical circuits into sparser and temporally extended modes of activity, potentially underlying the sparser population activity observed during task engagement and the stronger
shift in entropy flow per spike in competent mice. However, we did not observe the previously reported decoupling of neuronal activity during active engagement (Supplementary Fig. S5), which may suggest the involvement
of additional mechanisms beyond those described above.
In our analysis, the shift toward sparser activity during
active engagement was significantly correlated with behavioral performance (Fig. 10B), consistent with sparsecoding theories that posit efficient representations using a
few active neurons for natural images [81–83]. Moreover,
mice with higher task performance exhibited greater entropy flow per spike during active compared with passive conditions (Fig. 10E), indicating that the capacity to form economical image representations via timeasymmetric causal activity is also linked to behavioral
performance. Future work should determine whether this
pattern reflects a direct computational mechanism or a
secondary consequence of network state (e.g., attention
or arousal). Importantly, the proposed method further
yields testable predictions for information coding. For instance, if entropy flow per spike indeed relates to computation, then (i) neurons whose receptive fields match the
presented image features should show selectively higher
entropy flow per spike, or (ii) population decoding accuracy is expected to remain largely unchanged when the
analysis is restricted to neurons with higher entropy flow
per spike. Moreover, targeted pharmacological or optogenetic manipulations of neuromodulatory systems are
predicted to induce systematic changes in entropy flow
by modulating coupling variability, thereby altering coding efficiency. These predictions provide avenues to experimentally validate the computational role of entropy
flow.
EEG, fMRI, and ECoG studies suggest that steady-

state entropy production and related irreversibility metrics covary with consciousness level and cognitive load,
and they reveal large-scale directed temporal structure
[28–31, 84–87]. For example, in human fMRI, violations
of the fluctuation-dissipation theorem are larger during
wakefulness than deep sleep, and larger during tasks than
rest [85]. Arrow-of-time analyses likewise show stronger
temporal asymmetry during tasks than rest and identify a cortical hierarchy of asymmetry [86]. Our statespace kinetic Ising model complements these steadystate, macroscopic approaches by estimating entropy flow
directly from spiking data without assuming stationarity, potentially illuminating the lower-level mechanisms
of mesoscopic/microscopic circuit dynamics. In parallel, equilibrium Ising and energy-landscape methods have
been successfully applied to binarized neuroimaging and
electrophysiological signals to characterize correlation
structure and attractor basins of large-scale brain networks [88–91]. Our framework explicitly quantifies timeasymmetric entropy flow in nonstationary binary signals, complementing energy-landscape analyses of macroscopic stability with measures of time-dependent causal
dynamics. In principle, our approach could be extended
upward in scale to local field potentials (LFPs), multielectrode arrays (MEAs), or coarse-grained EEG/ECoG
recordings, enabling multiscale analysis of nonequilibrium dynamics from circuit to whole-brain levels.
In addition, our framework could be extended to analyze longer-term processes such as learning by treating
time bins as trials within sessions and allowing parameters to vary across sessions, under the assumption of stationarity within each session. This would enable tracing
learning trajectories of couplings among individual neurons when stable longitudinal recordings are available,
an increasingly feasible scenario with recent advances in
calcium imaging and electrophysiology [92, 93]. However,
the state-space method still faces limits in computational
time and scale, constraining its use for large-scale signals.
Future improvements through parallelization, optimized
algorithms, and refined mean-field approaches could extend its applicability and enhance entropy flow estimation.
The kinetic Ising-based framework should also be
viewed in light of its theoretical limitations. While
analytically tractable, it imposes strong assumptions –
namely, pairwise couplings and conditional independence
– that simplify neural dynamics but restrict interpretability. Our model misspecification analysis (Fig. 5) showed
that reproducing the heavy-tailed spike-count statistics
observed in real populations requires higher-order interactions; neglecting these leads to systematic biases,
particularly in the tails. Likewise, synchronous updates
imposed by conditional independence obscure cascadelike recruitment within bins in experimental data, leading to bin-size-dependent distortions: Large bins capture heavy tails by merging cascades, which the model
fails to represent, while small bins preserve fine-scale cascades, but the model misses slower interactions distant in

18
time. These limitations motivate extensions beyond the
synchronous pairwise framework. The generalized linear
models (GLMs) and related point-process models provide
a natural asynchronous alternative with longer historydependency, since spikes are modeled in fine-grained bins
or continuous time and influence others through coupling
kernels. However, entropy flow in such history-dependent
systems requires full path probabilities, making estimation challenging.
More broadly, fitted couplings and entropy flow should
be regarded as statistical summaries of nonequilibrium
dynamics, not direct measures of synaptic connectivity or mechanism. Future work must relax these constraints –by permitting asynchronous updates, incorporating higher-order dependencies, and developing principled estimators of entropy flow in non-Markovian settings
–while remaining clear about the limits of inference when
bridging statistical abstractions with physiology. For example, the alternating-shrinking higher-order interaction
model (Eq. 63) could be extended to include asymmetric couplings, potentially with asynchronous updates in
a continuous-time limit.
In summary, by developing a state-space kinetic Ising
model that accounts for both nonstationary and nonequilibrium properties, we have demonstrated how task engagement modulates neuronal firing activity and coupling
diversity. Our approach incorporates time-varying entropy flow estimation, revealing that time-asymmetric,
irreversible activity emerges within sparsely active populations during task engagement—an effect correlated
with the mouse’s behavioral performance. These findings underscore the utility of our approach, offering new
insights into the thermodynamic underpinnings of neural
computation.

METHODS
Estimating time-varying parameters of the kinetic
Ising model

We summarize the expectation-maximization algorithm for estimating the state-space kinetic Ising model
with optimized hyperparameters. See Supplementary
Note 1 for more details.
E-step: Given the hyperparameters w, we obtain the
estimate of the state θ t given all the data available.
When estimating the parameters θ it (t = 0, 1, . . . , T ,
i = 1, . . . , N ) from the spike data xt (t = 0, 1, . . . , T ), we
first obtain the filter density by the sequentially applying
the Bayes theorem:
p(xt |θ t , x0:t−1 , w)p(θ t |x0:t−1 , w)
p(θ t |x0:t , w) =
. (22)
p(xt |x0:t−1 , w)
Here, the one-step prediction density is computed using

the Chapman-Kolmogorov equation:
p(θ t |x0:t−1 , w) =

N Z
Y

p(θ it |θ it−1 , Qi )p(θ it−1 |xt−1 )dθ it−1 .

i=1

(23)
By assuming that the filter density for the i-th neuron at
the previous time step t − 1 is given by the Gaussian disi
,
tribution with mean θ it−1|t−1 and covariance Wt−1|t−1
the one-step prediction density becomes the Gaussian
i
distribution whose mean θ it|t−1 and covariance Wt|t−1
are given by
θ it|t−1 = θ it−1|t−1 ,

(24)

i
i
= Wt−1|t−1
+ Qi ,
Wt|t−1

(25)

i
with θ i1|0 = µi and W1|0
= Σi being the hyperparam-

eters of the initial Gaussian distribution, p(θ i1 |µi , Σi ).
Then, the filter density is given as
p(θ t |x0:t , w) =

N
Y

p(θ it |x0:t , w)

i=1

∝

N Y
L
Y


exp θi,t xli,t +

i=1 l=1

N
X


θij,t xlit xlj,t−1 − ψ(θ it , xlt−1 )

j=1

N
Y



1 i
i
i
⊤
i
−1 i
·
exp − (θ t − θ t|t−1 ) (Wt|t−1 ) (θ t − θ t|t−1 ) .
2
i=1
(26)
Since this filter density is a concave function with respect to θ it for each neuron, we apply the Laplace approximation independently to the filter densities of individual neurons and obtain the approximate Gaussian
distributions, where the mean is approximated by the
MAP estimate:
log p(θ it |x0:t , w),
θ it|t = arg max
i

(27)

θt

for i = 1, . . . , N , while the covariance is approximated
using the Hessian as
"
#−1
i
2
∂
log
p(θ
|x
,
w)
0:t
t
i
Wt|t
= −
T
θ it =θ it|t
∂θ it ∂ θ it


−1 −1
i
= G(θ it|t ) + Wt|t−1
,
(28)
where G(θ it ) ≡

PL

l=1

∂ 2 ψ(θ it ,xlt−1 )
∂θ it ∂ (θ it )

T

is the Fisher

θ it =θ it|t
information matrix with respect to θ it computed for the

kinetic Ising model over the trials. We computed the
MAP estimate by the Newton-Raphson method utilizing
the Hessian evaluated at a search point.
Next, we obtain the smoother density by recursively
applying the formula below. Because the filter density

19
and state transitions are approximated by normal distributions, we follow the fixed-interval smoothing algorithm developed for the Gaussian distributions [94]. In
this method, the smoothed mean and covariance are recursively obtained by the following equations:


θ it−1|T = θ it−1|t−1 + Ait−1 θ it|T − θ it|t ,
(29)


i
i
i
i
Wt−1|T
= Wt−1|t−1
+ Ait−1 Wt|T
− Wt|t
Ai⊤
t−1 ,
(30)


i
i
Ait−1 = Wt−1|t−1
Wt|t−1

−1

,

σtflow = −σtforward + σtbackward ,

i
Σi = W1|T
+ (θ i1|T − µ)(θ i1|T − µ)⊤ .

X

σtforward = −

p(xt , xt−1 ) log p(xt |xt−1 ),

(36)

p(xt , xt−1 ) log p(xt−1 |xt ).

(37)

xt ,xt−1

X

σtbackward = −

xt ,xt−1

We calculate these conditional entropies using the Gaussian approximation as follows.
We begin with approximating the forward conditional
entropy as
σtforward = −

X

p(xt |xt−1 )p(xt−1 ) log p(xt |xt−1 )

xt ,xt−1

T
1 Xh i
(θ t|T − θ it−1|T )(θ it|T − θ it−1|T )⊤
T − 1 t=2
i
i
i
i
i
+Wt|T
− Wt−1,t|T
− Wt,t−1|T
+ Wt−1|T
. (32)

We compute the lag-one smoothing covariance matrix
i
Wt,t−1|T
following the method of De Jong and Macki
i
i
i
innon [95]: Wt,t−1|T
= Wt|t
(Wt+1|t
)−1 Wt|T
. We also
note that the optimization of a diagonal of the form
Qi = diag[λi0 , . . . , λiN ] or Qi = λi I can be performed
by taking diagonal and trace of the r.h.s of the equation
above, respectively.
Similarly, we update Σi according to

(35)

where

(31)

for t = T, T − 1, . . . , 2.
M-step: We optimize the hyperparameters given the
smoothed posteriors. To optimize the hyperparameter
Qi , we used the following update formula that maximizes
the lower bound of the log marginal likelihood:
Qi =

First, σtflow can be decomposed as follows by introducing the forward and backward conditional entropies:

≃−

X

Q(xt−1 )

xt−1

X

p(xt |xt−1 ) log p(xt |xt−1 ).

xt

(38)
Here we replaced p(xt−1 ) with an independent model
Q(xt−1 ) defined as
Q(xt−1 ) =

Y

Q(xi,t−1 ).

(39)

i

The conditional probability is written as
p(xt |xt−1 ) =

Y

p(xi,t |xt−1 ),

(40)

i

(33)
where

The convergence of the EM algorithm is assessed by
computing the approximate log marginal likelihood function (Eq.6) using the Laplace approximation. Using the
mean and covariance of the filter and one-step prediction densities, the approximate log marginal likelihood
function for the hyperparameters w is obtained as
log p(x0:T |w) = log p(x0 )

T X
N 
X
1
1
i
i
+
log |Wt|t
| − log |Wt|t−1
| + q(θ it|t ) .
2
2
t=1 i=1
(34)
See Supplementary Note 1 for the derivations, and the
functional form of q(·).

p(xi,t |xt−1 ) = exi,t hi,t (xt−1 )−ψ(hi,t (xt ))
with
hi,t (xt−1 ) = θi,t +

Here we extend the mean-field approximation method
developed for the steady-state kinetic Ising model [43] to
make it applicable to nonstationary systems.

X

θij,t xj,t−1 .

(42)

j

Here, we redefined the log normalization function ψ as a
function of hi,t (xt ): ψ(hi,t (xt )) = log(1 + ehi,t (xt ) ).
Note that the expectation of xi,t is given by
r(hi,t (xt−1 )) =

X

xi,t p(xi,t |xt−1 )

xi,t

=
Mean-field approximation of the entropy flow

(41)

1
.
1 + e−hi,t (xt−1 )

(43)

Using r(hi,t (xt−1 )), we have
p(xi,t = 1|xt−1 ) = r(hi,t (xt−1 )),
p(xi,t = 0|xt−1 ) = 1 − r(hi,t (xt−1 )).

(44)
(45)

20
Next, we approximate σtbackward . It is computed as

Then the forward conditional entropy becomes
σtforward ≃ −

X
xt−1

·

p(xi,t |xt−1 ) log p(xi,t |xt−1 )

Q(xt−1 )χ (hi,t (xt−1 )) ,

(46)

=−
·

where
X

xt−2

X X

p(xt−1 |xt−2 )p(xt−2 )

X

p(xt |xt−1 )

X

= −r(hi,t (xt−1 )) log r(hi,t (xt−1 ))
− (1 − r(hi,t (xt−1 ))) log(1 − r(hi,t (xt−1 )))
= −[r(hi,t (xt−1 ))hi,t (xt−1 ) − ψ(hi,t (xt ))]

(53)
We approximate the following probabilities by independent distributions:



Dz χ gi,t,t−1 + z

p



∆i,t,t−1 ,

p(xt−2 ) = Q(xt−2 ),
p(xt |xt−1 ) = Q(xt ).

(47)

We approximate Eq. 46 by a Gaussian distribution
based on the central limit theorem for a collection of independent binary
 signals. Specifically, by using Dz =
√dz exp − 1 z 2 , the forward conditional entropy is ap2
2π
proximated as
σtforward ≈

[xi,t−1 hi,t (xt ) − ψ(hi,t (xt ))] .

i

p(xi,t |xt−1 ) log p(xi,t |xt−1 )

xi,t

XZ

p(xt−1 |xt−2 )p(xt−2 ) log p(xt−1 |xt )

xt ,xt−1

xt

χ (hi,t (xt−1 )) ≡ −

X

p(xt |xt−1 )

xt−2 xt−1

xt−1

i

X

=−

xi,t

XX

=

p(xt , xt−1 ) log p(xt−1 |xt )

xt ,xt−1

XX
i

X

σtbackward = −

Q(xt−1 )

Using them, σtbackward can be approximated as
σtbackward ≃ −
X

(48)

Q(xt )

xt

=−

where gi,t,t−1 and ∆i,t,t−1 are the mean and variance of
hi,t (xt−1 ) given by

X X

p(xt−1 |xt−2 )Q(xt−2 )

xt−2 xt−1

·

i

(54)
(55)

[xi,t−1 hi,t (xt ) − ψ(hi,t (xt ))]

i

X

Q(xt )

xt

·

X

X

X

Q(xt−2 )

xt−2

[r(hi,t−1 (xt−2 ))hi,t (xt ) − ψ(hi,t (xt ))]

i

gi,t,t−1 = θi,t +

X

θij,t mj,t−1 ,

(49)

=−

j

∆i,t,t−1 =

X

i

2
θij,t
mj,t−1 (1 − mj,t−1 ).

(50)

j

Here, mi,t is the mean-field approximation of xi,t obtained by the Gaussian approximation method assuming
independent activity of neurons at t − 1:
mi,t =

X

xi,t p(xt |xt−1 )p(xt−1 )

xt ,xt−1

=

X

ϕi,t (hi,t (xt )) = −[mi,t−1 hi,t (xt ) − ψ(hi,t (xt ))],

Q(xt−1 )r(hi,t (xt−1 )).

(51)

Dz r gi,t,t−1 + z

p



∆i,t,t−1 ,

(52)

XX
i

≈



(57)

the backward conditional entropy is obtained by the
Gaussian integral:
σtbackward =

Applying the Gaussian approximation to hi,t (xt−1 ), mi,t
is recursively computed as
mi,t ≈

Q(xt ) [mi,t−1 hi,t (xt ) − ψ(hi,t (xt ))] , (56)

xt

where we used Eq. 43 to obtain the second equality and
Eq. 51 to obtain the last result. By defining

xt−1

Z

XX

Q(xt )ϕi,t (hi,t (xt ))

xt

XZ



p
Dz ϕi,t gi,t,t + z ∆i,t,t ,

(58)

i

where
gi,t,t ≡ θi,t +

X

θij,t mj,t ,

(59)

2
θij,t
mj,t (1 − mj,t ).

(60)

j

for t = 1, . . . , T , using Eqs. 49 and 50, which are functions
of mi,t−1 . Here mi,1 was computed using nominal values
of mi,0 (i = 1, . . . , N ). In the simulation and empirical
analyses, we used spiking probability averaged over all
time steps and trials for each neuron as mi,0 .

∆i,t,t =

X
j

An alternative approach to obtain the backward conditional entropy is given in Supplementary Note 2.

21
Thus, the entropy flow is obtained as

Alternating-shrinking higher-order interaction
model

σtflow = −σtforward + σtbackward
"


XZ
p
≈
Dz − χ gi,t,t−1 + z ∆i,t,t−1
i



+ ϕi,t gi,t,t + z

p

∆i,t,t



#
,

(61)

which allows us to examine the contributions of each neuron to the total entropy flow.
See also Supplementary Note 3 for the analytical expression of the entropy flow under steady-state conditions
or for independent neurons.

To perform the analysis on fitting the kinetic Ising
model to a mismatched model, we generated binary spike
sequences using a nonlinearity that goes beyond linear synaptic summation and a logistic activation function, which therefore induces the higher-order interactions (HOIs) in the population activity. For this goal,
we employed the recently proposed alternating-shrinking
HOI model [58].
The model is a time-independent, homogeneous model
including all orders of HOIs in the following form:
P



N
j
P
N
h
X
i=1 xi
x
j+1
i i
,
p(x) =
exp −f
(−1)
Cj
Z
N
j=1
(63)

Generation of field and coupling parameters for
simulation studies

We constructed time-varying field and coupling parameters, from which we generated the binary data. To ensure smooth temporal variations, each coupling parameter θij,t was sampled from a Gaussian process of size
T with mean µ and covariance matrix defined by the
squared exponential kernel


(t − s)2
k(t, s) = k0 exp −
.
2τ 2

(62)

For the analysis of estimation error and computational time using different system sizes (Fig. 3), we used
the scaling mean µ = 5/N and variance k0 = 10/N ,
following the convention of the Sherrington-Kirkpatrick
model. √
The characteristic length-scale was specified by
τ = 30/ N . Similarly, the external field parameters θi,t
were independently sampled from the Gaussian process,
using µ = −3, τ = 50, and k0 = 1.
To obtain trajectories for the different system sizes, a
single set of random values was generated for the maximum system size, and subsets of these values were used
to examine the system size N . Specifically, for the coupling parameters, a global three-dimensional array was
created with dimensions corresponding to the maximum
number of neurons, time steps, and coupling connections.
Similarly, for the field parameters, a two-dimensional array was generated, with dimensions corresponding to the
maximum number of time steps and neurons. For a given
neuron count N , the relevant subset of values was extracted from these precomputed arrays, ensuring that
each N used a subset of the values assigned to larger
N . This hierarchical structure ensured that the seed for
N = 80 encompassed all values used for smaller N , maintaining consistency across different system sizes. We evaluated the model’s performance using this data set and
repeated the procedure 10 times.

where f is a sparsity parameter and Z is the partition
PN
function. Let n = i=1 xi . h (n) is an entropy-canceling
base measure function defined using the binomial coefficient:
 
N
h (n) = 1
.
(64)
n
The parameters C1 , C2 , . . . , CN are the shrinking paramj
eters, where Cj = (τ ) with 0 < τ < 1 results in the
shifted-geometric population spike-count distribution.
The population spike-count distribution is the probability distribution of n active neurons in the binary patterns, which is given as
 
N
P (n) =
p (x1 = 1, . . . , xn = 1, xn+1 = 0, . . . , xN = 0)
n


 
N
 n j
X
N h (n)
j+1
.
=
exp −f
(−1)
Cj
n
Z
N
j=1
(65)
This distribution was shown to be widespread due to the
cancellation of the binomial term, and also sparse due to
the alternating HOIs.
We performed Gibbs sampling from this distribution,
which dictates the dynamics of a recurrent neural network with threshold-supralinear
activation nonlinearity.
P
For neuron i, let ñ = j̸=i xj be the spike count of the
other units, and define
Q(ñ) =

N
X
j=1

j+1

(−1)


Cj

ñ
N

j
,

(66)

∆Q(ñ) = Q(ñ+1) − Q(ñ).

(67)

The unnormalized joint activities of neurons are

p0 ∝ h(ñ) exp −f Q(ñ)
(xi = 0),

p1 ∝ h(ñ+1) exp −f Q(ñ+1)
(xi = 1).

(68)
(69)

22
We update xi using the following conditional probability
given the state of all other neurons:
p(xi = 1|x\i ) =

1
.
1 + exp − log(p1 /p0 )

(70)

The log-ratio simplifies to
log



p1
= log h(ñ+1) − log h(ñ) − f ∆Q(ñ)
p0


ñ + 1
− f ∆Q(ñ).
(71)
= log
N − ñ

One sweep visits all i = 1, . . . , N in permuted order and
applies this update. We obtained 1,000,000 samples.
The resulting spike sequences were then fitted with the
state-space kinetic Ising model. Because the data were
stationary, we fixed the state noise covariance to zero,
Qi = 0 (i = 1, . . . , N ), and omitted hyperparameter optimization. To reduce computation time, the samples
were reorganized into T = 200 time bins and L = 5000
trials, preserving dependencies across consecutive bins
within each trial. Under this setting, the fitted statespace model yielded constant parameters across bins. We
then generated 500,000 spike sequences by resampling
from the fitted model, and compared their population
spike-count distribution with that of the original Gibbssampled data.

DATA AVAILABILITY

We used the publicly available Allen Brain Observatory: Visual Behavior Neuropixels dataset provided by
the Allen Institute for Brain Science:
https://portal.brain-map.org/circuits-behavior/visualbehavior-neuropixels.
Large precomputed datasets required to reproduce the
figures are archived on Zenodo:
doi:10.5281/zenodo.15220108.

CODE AVAILABILITY

The analysis code used in this study is archived on
Zenodo and linked to the GitHub repository:
doi:10.5281/zenodo.17504162.
For convenient browsing, see the GitHub mirror:
https://github.com/KenIshihara-17171ken/Non equ.

REFERENCES
[1] Schrödinger, E. What is Life?: The Physical Aspect of the
Living Cell (Cambridge University Press, 1944).
[2] Prigogine, I. & Stengers, I. Order Out of Chaos: Man’s
New Dialogue with Nature. Bantam new age books (Bantam Books, 1984).

[3] Kondepudi, D. & Prigogine, I. Modern thermodynamics:
from heat engines to dissipative structures (John wiley &
sons, 2014).
[4] Eigen, M. & Winkler, R. Laws of the game: how the principles of nature govern chance, vol. 10 (Princeton University Press, 1993).
[5] Schneider, E. D. & Kay, J. J. Life as a manifestation of
the second law of thermodynamics. Math. Comput. Model.
19, 25–48 (1994).
[6] Schnakenberg, J. Network theory of microscopic and
macroscopic behavior of master equation systems. Rev.
Mod. Phys. 48, 571–585 (1976).
[7] Crooks, G. E. Entropy production fluctuation theorem
and the nonequilibrium work relation for free energy differences. Phys. Rev. E 60, 2721 (1999).
[8] Evans, D. J. & Searles, D. J. The fluctuation theorem.
Adv. Phys. 51, 1529–1585 (2002).
[9] Seifert, U. Stochastic thermodynamics, fluctuation theorems and molecular machines. Rep. Prog. Phys. 75, 126001
(2012).
[10] Barato, A. C. & Seifert, U. Thermodynamic uncertainty
relation for biomolecular processes. Phys. Rev. Lett. 114,
158101 (2015).
[11] Gingrich, T. R., Horowitz, J. M., Perunov, N. & England, J. L. Dissipation bounds all steady-state current
fluctuations. Phys. Rev. Lett. 116, 120601 (2016).
[12] Proesmans, K. & Van den Broeck, C. Discrete-time thermodynamic uncertainty relation. Europhys. Lett. 119,
20001 (2017).
[13] Aguilera, M., Ito, S. & Kolchinsky, A. Inferring entropy
production in many-body systems using nonequilibrium
maxent. arXiv preprint arXiv:2505.10444 (2025).
[14] Shiraishi, N., Funo, K. & Saito, K. Speed limit for classical stochastic processes. Phys. Rev. Lett. 121, 070601
(2018).
[15] Van Vu, T. & Saito, K. Thermodynamic unification of
optimal transport: Thermodynamic uncertainty relation,
minimum dissipation, and thermodynamic speed limits.
Phys. Rev. X 13, 011013 (2023).
[16] Churchland, M. M. et al. Neural population dynamics
during reaching. Nature 487, 51–56 (2012).
[17] Kuzmina, E., Kriukov, D. & Lebedev, M. Neuronal travelling waves explain rotational dynamics in experimental
datasets and modelling. Sci. Rep. 14, 3566 (2024).
[18] Skaggs, W. E. & McNaughton, B. L. Replay of neuronal
firing sequences in rat hippocampus during sleep following
spatial experience. Science 271, 1870–1873 (1996).
[19] Lee, A. K. & Wilson, M. A. Memory of sequential experience in the hippocampus during slow wave sleep. Neuron
36, 1183–1194 (2002).
[20] Harris, K. D., Csicsvari, J., Hirase, H., Dragoi, G. &
Buzsáki, G. Organization of cell assemblies in the hippocampus. Nature 424, 552–556 (2003).
[21] Hebb, D. O. The Organization of Behavior: A Neuropsychological Theory (Wiley, New York, 1949).
[22] Abeles, M. Corticonics: Neural circuits of the cerebral
cortex (Cambridge University Press, 1991).
[23] Diesmann, M., Gewaltig, M.-O. & Aertsen, A. Stable
propagation of synchronous spiking in cortical neural networks. Nature 402, 529–533 (1999).
[24] Harris, K. D. Neural signatures of cell assembly organization. Nat. Rev. Neurosci. 6, 399–407 (2005).
[25] Izhikevich, E. M. Polychronization: computation with
spikes. Neural Comput. 18, 245–282 (2006).

23
[26] Ito, S., Oizumi, M. & Amari, S.-i. Unified framework
for the entropy production and the stochastic interaction
based on information geometry. Phys. Rev. Res. 2, 033048
(2020).
[27] Yang, Y.-J. & Qian, H. Unified formalism for entropy
production and fluctuation relations. Phys. Rev. E 101,
022129 (2020).
[28] Perl, Y. S. et al. Nonequilibrium brain dynamics as a signature of consciousness. Phys. Rev. E 104, 014411 (2021).
[29] de la Fuente, L. A. et al. Temporal irreversibility of neural
dynamics as a signature of consciousness. Cereb. Cortex.
(2022).
[30] Gilson, M., Tagliazucchi, E. & Cofré, R. Entropy production of multivariate ornstein-uhlenbeck processes correlates with consciousness levels in the human brain. Phys.
Rev. E 107, 024121 (2023).
[31] Sekizawa, D., Ito, S. & Oizumi, M. Decomposing thermodynamic dissipation of linear langevin systems via oscillatory modes and its application to neural dynamics. Phys.
Rev. X 14, 041003 (2024).
[32] Lynn, C. W., Cornblath, E. J., Papadopoulos, L.,
Bertolero, M. A. & Bassett, D. S. Broken detailed balance and entropy production in the human brain. Proc.
Natl. Acad. Sci. U.S.A. 118 (2021).
[33] Crisanti, A. & Sompolinsky, H. Dynamics of spin systems with randomly asymmetric bonds: Langevin dynamics and a spherical model. Phys. Rev. A 36, 4922 (1987).
[34] Crisanti, A. & Sompolinsky, H. Dynamics of spin systems
with randomly asymmetric bonds: Ising spins and glauber
dynamics. Phys. Rev. A 37, 4865 (1988).
[35] Schneidman, E., Berry, M. J., Segev, R. & Bialek, W.
Weak pairwise correlations imply strongly correlated network states in a neural population. Nature 440, 1007–1012
(2006).
[36] Tkačik, G. et al. Thermodynamics and signatures of criticality in a network of neurons. Proc. Natl. Acad. Sci.
U.S.A. 112, 11508–11513 (2015).
[37] Aguilera, M., Igarashi, M. & Shimazaki, H. Nonequilibrium thermodynamics of the asymmetric sherringtonkirkpatrick model. Nat. Commun. 14, 3685 (2023).
[38] Kappen, H. & Spanjers, J. Mean field theory for asymmetric neural networks. Phys. Rev. E 61, 5658 (2000).
[39] Roudi, Y. & Hertz, J. Dynamical tap equations for nonequilibrium ising spin glasses. J. Stat. Mech.: Theory Exp.
2011, P03031 (2011).
[40] Roudi, Y. & Hertz, J. Mean field theory for nonequilibrium network reconstruction. Phys. Rev. Lett. 106, 048702
(2011).
[41] Mézard, M. & Sakellariou, J. Exact mean-field inference
in asymmetric kinetic ising systems. J. Stat. Mech.: Theory Exp. 2011, L07001 (2011).
[42] Sakellariou, J., Roudi, Y., Mezard, M. & Hertz, J. Effect of coupling asymmetry on mean-field solutions of the
direct and inverse sherrington–kirkpatrick model. Philos.
Mag. 92, 272–279 (2012).
[43] Aguilera, M., Moosavi, S. A. & Shimazaki, H. A unifying
framework for mean-field theories of asymmetric kinetic
ising systems. Nat. Commun. 12, 1197 (2021).
[44] Brown, E. N., Frank, L. M., Tang, D., Quirk, M. C. &
Wilson, M. A. A statistical paradigm for neural spike train
decoding applied to position prediction from ensemble firing patterns of rat hippocampal place cells. J. Neurosci.
18, 7411–7425 (1998).

[45] Yu, B. M. et al. Gaussian-process factor analysis for
low-dimensional single-trial analysis of neural population
activity. Adv. Neural Inf. Process. Syst. 21 (2008).
[46] Shimazaki, H., Amari, S.-i., Brown, E. N. & Grun, S.
State-space analysis on time-varying correlations in parallel spike sequences. In Proc. IEEE Int. Conf. Acoust.
Speech Signal Process., 3501–3504 (IEEE, 2009).
[47] Shimazaki, H., Amari, S.-i., Brown, E. N. & Grün, S.
State-space analysis of time-varying higher-order spike
correlation for multiple neural spike train data. PLOS
Comput. Biol. 8, e1002385 (2012).
[48] Donner, C., Obermayer, K. & Shimazaki, H. Approximate inference for time-varying interactions and macroscopic dynamics of neural populations. PLOS Comput.
Biol. 13, e1005309 (2017).
[49] Gaudreault, J. & Shimazaki, H. State-space analysis of
an ising model reveals contributions of pairwise interactions to sparseness, fluctuation, and stimulus coding of
monkey v1 neurons. In Artif. Neural Netw. Mach. Learn.–
ICANN 2018, Proc., Part III 27, 641–651 (Springer,
2018).
[50] Gaudreault, J., Saxena, A. & Shimazaki, H. Online estimation of multiple dynamic graphs in pattern sequences.
In Proc. Int. Jt. Conf. Neural Netw., 1–8 (IEEE, 2019).
[51] Shumway, R. H. & Stoffer, D. S. An approach to time
series smoothing and forecasting using the em algorithm.
J. Time Ser. Anal. 3, 253–264 (1982).
[52] Smith, A. C. & Brown, E. N. Estimating a state-space
model from point process observations. Neural Comput.
15, 965–991 (2003).
[53] Wolpert, D. H. et al. Is stochastic thermodynamics the
key to understanding the energy costs of computation?
Proc. Natl. Acad. Sci. U.S.A. 121, e2321112121 (2024).
[54] Dempster, A. P., Laird, N. M. & Rubin, D. B. Maximum
likelihood from incomplete data via the em algorithm. J.
R. Stat. Soc. Ser. B (Methodol.) 39, 1–22 (1977).
[55] Gaspard, P. Time-reversed dynamical entropy and irreversibility in markovian random processes. J. Stat. Phys.
117, 599–615 (2004).
[56] Cofré, R., Videla, L. & Rosas, F. An introduction to the
non-equilibrium steady states of maximum entropy spike
trains. Entropy 21, 884 (2019).
[57] Igarashi, M.
Entropy production for discrete-time
markov processes.
arXiv preprint arXiv:2205.07214
(2022).
[58] Rodrıguez-Domınguez, U. & Shimazaki, H. Modeling
higher-order interactions in sparse and heavy-tailed neural population activity. Neural Comput. 37, 2011–2078
(2025).
[59] Amari, S.-i., Nakahara, H., Wu, S. & Sakai, Y. Synchronous firing and higher-order interactions in neuron
pool. Neural Comput. 15, 127–142 (2003).
[60] Siegle, J. H. et al. Survey of spiking in the mouse visual
system reveals functional hierarchy. Nature 592, 86–92
(2021).
[61] Nitzan, N., Bennett, C., Movshon, J. A., Olsen, S. R. &
Buzsáki, G. Mixing novel and familiar cues modifies representations of familiar visual images and affects behavior.
Cell Rep. 43 (2024).
[62] Ito, S. et al. Coordinated changes in a cortical circuit
sculpt effects of novelty on neural dynamics. Cell Rep. 43
(2024).
[63] Rolls, E. T. & Tovee, M. J. Sparseness of the neuronal
representation of stimuli in the primate temporal visual

24
cortex. J. Neurophysiol. 73, 713–726 (1995).
[64] Donner, C. & Opper, M. Inverse ising problem in continuous time: A latent variable approach. Phys. Rev. E 96,
062104 (2017).
[65] Delamare, G. & Ferrari, U. Time-dependent maximum
entropy model for populations of retinal ganglion cells. In
Phys. Sci. Forum, vol. 5, 31 (2022).
[66] Granot-Atedgi, E., Tkačik, G., Segev, R. & Schneidman,
E. Stimulus-dependent maximum entropy models of neural population codes. PLOS Comput. Biol. 9, e1002922
(2013).
[67] Campajola, C., Gangi, D. D., Lillo, F. & Tantari, D.
Modelling time-varying interactions in complex systems:
the score driven kinetic ising model. Sci. Rep. 12, 19339
(2022).
[68] Pho, G. N., Goard, M. J., Woodson, J., Crawford, B. &
Sur, M. Task-dependent representations of stimulus and
choice in mouse parietal cortex. Nat. Commun. 9, 2596
(2018).
[69] Dadarlat, M. C. & Stryker, M. P. Locomotion enhances
neural encoding of visual stimuli in mouse v1. J. Neurosci.
37, 3764–3775 (2017).
[70] Christensen, A. J. & Pillow, J. W. Reduced neural activity but improved coding in rodent higher-order visual
cortex during locomotion. Nat. Commun. 13, 1676 (2022).
[71] Froudarakis, E. et al. Population code in mouse v1 facilitates readout of natural scenes through increased sparseness. Nat. Neurosci. 17, 851–857 (2014).
[72] Yoshida, T. & Ohki, K. Natural images are reliably represented by sparse and variable populations of neurons in
visual cortex. Nat. Commun. 11, 872 (2020).
[73] Renart, A. & Machens, C. K. Variability in neural activity and behavior. Curr. Opin. Neurobiol. 25, 211–220
(2014).
[74] Brinkman, B. A., Rieke, F., Shea-Brown, E. & Buice,
M. A. Predicting how and when hidden neurons skew
measured synaptic interactions. PLOS Comput. Biol. 14,
e1006490 (2018).
[75] Montijn, J. S., Goltstein, P. M. & Pennartz, C. M. Mouse
v1 population correlates of visual detection rely on heterogeneity within neuronal response patterns. Elife 4, e10163
(2015).
[76] Runfeldt, M. J., Sadovsky, A. J. & MacLean, J. N.
Acetylcholine functionally reorganizes neocortical microcircuits. J. Neurophysiol. 112, 1205–1216 (2014).
[77] Chen, N., Sugihara, H. & Sur, M. An acetylcholineactivated microcircuit drives temporal dynamics of cortical activity. Nat. Neurosci. 18, 892–902 (2015).
[78] Reitman, M. E. et al. Norepinephrine links astrocytic
activity to regulation of cortical state. Nat. Neurosci. 26,
579–593 (2023).
[79] Lee, S.-H. & Dan, Y. Neuromodulation of brain states.
Neuron 76, 209–222 (2012).
[80] McCormick, D. A., Nestvogel, D. B. & He, B. J. Neuromodulation of brain state and behavior. Annu. Rev.
Neurosci. 43, 391–415 (2020).
[81] Olshausen, B. A. & Field, D. J. Emergence of simplecell receptive field properties by learning a sparse code for
natural images. Nature 381, 607–609 (1996).
[82] Olshausen, B. A. & Field, D. J. Sparse coding with an
overcomplete basis set: A strategy employed by v1? Vision Res. 37, 3311–3325 (1997).
[83] Foldiak, P. Sparse coding in the primate cortex. The
handbook of brain theory and neural networks 895–898

(2003).
[84] Deco, G., Sanz Perl, Y., Bocaccio, H., Tagliazucchi, E.
& Kringelbach, M. L. The insideout framework provides
precise signatures of the balance of intrinsic and extrinsic
dynamics in brain states. Commun. Biol. 5, 572 (2022).
[85] Deco, G., Lynn, C. W., Sanz Perl, Y. & Kringelbach,
M. L. Violations of the fluctuation-dissipation theorem
reveal distinct nonequilibrium dynamics of brain states.
Phys. Rev. E 108, 064410 (2023).
[86] Deco, G. et al. The arrow of time of brain signals in
cognition: Potential intriguing role of parts of the default
mode network. Netw. Neurosci. 7, 966–998 (2023).
[87] Kringelbach, M. L., Perl, Y. S. & Deco, G. The thermodynamics of mind. Trends Cogn. Sci. 28, 568–581 (2024).
[88] Watanabe, T. et al. A pairwise maximum entropy model
accurately describes resting-state human brain networks.
Nat. Commun. 4, 1370 (2013).
[89] Ezaki, T., Watanabe, T., Ohzeki, M. & Masuda, N. Energy landscape analysis of neuroimaging data. Philos.
Trans. R. Soc. A 375, 20160287 (2017).
[90] Masuda, N., Islam, S., Thu Aung, S. & Watanabe, T.
Energy landscape analysis based on the ising model: Tutorial review. PLOS Complex Syst. 2, e0000039 (2025).
[91] Watanabe, T. & Yamasue, H. Noninvasive reduction of
neural rigidity alters autistic behaviors in humans. Nat.
Neurosci. 28, 1348–1360 (2025).
[92] Steinmetz, N. A. et al. Neuropixels 2.0: A miniaturized
high-density probe for stable, long-term brain recordings.
Science 372, eabf4588 (2021).
[93] van Beest, E. H. et al. Tracking neurons across days with
high-density probes. Nat. Methods. 22, 778–787 (2025).
[94] Rauch, H. E., Tung, F. & Striebel, C. T. Maximum
likelihood estimates of linear dynamic systems. AIAA J.
3, 1445–1450 (1965).
[95] Jong, P. D. & Mackinnon, M. J. Covariances for
smoothed estimates in state space models. Biometrika
75, 601–602 (1988).

ACKNOWLEDGMENTS

We thank Shinji Nakaoka for his kind support of this
project. This work was supported by JSPS KAKENHI
Grant Number JP 20K11709, 21H05246, 24K21518,
25K03085 (H.S.).

AUTHOR CONTRIBUTIONS

K.I. developed the algorithms, implemented the code,
and performed the data analyses. H.S. conceived and
supervised the project and contributed to analyses. Both
authors wrote and revised the manuscript.

COMPETING INTERESTS

The authors declare no competing interests.

1

State-space kinetic Ising model reveals task-dependent entropy flow in sparsely active
nonequilibrium neuronal dynamics
Supplementary Information
Ken Ishihara
Graduate School of Life Science, Hokkaido University, Sapporo, Japan
Center for Human Nature, Artificial Intelligence,
and Neuroscience (CHAIN), Hokkaido University, Sapporo, Japan
Hideaki Shimazaki
Graduate School of Informatics, Kyoto University, Kyoto, Japan
Center for Human Nature, Artificial Intelligence,
and Neuroscience (CHAIN), Hokkaido University, Sapporo, Japan

Supplementary Note 1: State-space kinetic Ising model

In this Supplementary Note, we provide the filtering and smoothing algorithms for the time-varying kinetic Ising
model and an optimization method of its hyperparameters via the Expectation-Maximization algorithm.

1.

Model

Let xi,t = {0, 1} be an outcome of a binary random variable of neuron i at time t (i = 1, . . . , N , t = 0, . . . , T ). In
the kinetic Ising model, the activation of neuron i at time t independently depends on the activities of the neurons in
the previous time step t − 1. The conditional probability mass function of xi,t is given as
h
i
PN
exp θi,t xi,t + j=1 θij,t xi,t xj,t−1
h
i ,
p(xi,t |x1,t−1 , . . . , xN,t−1 , θ it ) =
(S1.1)
PN
1 + exp θi,t + j=1 θij,t xj,t−1
where θi,t is a time-dependent field parameter that determines the bias for inputs to the i-th neuron at time t, and
θij,t is a time-dependent coupling parameter from the j-th neuron to the i-th neuron at time t. These parameters are
collectively denoted as θ it = (θi,t , θi1,t , . . . θij,t , . . . θiN,t ). Using the log normalization function,



N
X
ψ(θ it , xlt−1 ) = log 1 + exp θi,t +
θij,t xlj,t−1  ,
(S1.2)
j=1

the kinetic Ising model is also written as

p(xi,t |x1,t−1 , . . . , xN,t−1 , θ it ) = exp θi,t xi,t +

N
X


θij,t xi,t xj,t−1 − ψ(θ it , xt−1 ) .

(S1.3)

j=1

Assuming conditional independence, the joint probability mass function that determines the probabilities of generating
patterns of activity across N neurons is given by
N
Y

p(xi,t |x1,t−1 , . . . , xN,t−1 , θ it ).

(S1.4)

i=1

Typical neurophysiological experiments repeat multiple trials of measurement under the same experimental conditions. We let xli,t = {0, 1} be a binary variable of the i-th neuron at time t in the l-th trial (i = 1, . . . , N ,
t = 0, . . . , T , l = 1, . . . , L). We collectively denote the binary patterns of simultaneously recorded neurons at time
t in the l-th trial using a vector, xlt = (xl1,t , . . . , xlN,t ). Further, we denote the patterns at time t from all trials
by xt = (x1t , . . . , xlt , . . . , xL
t ) and denote all the patterns up to time t by x0:t . We use the same convention for the
time-varying parameters, denoting them as θ t = (θ 1t , . . . , θ it , . . . , θ N
t ) and θ 1:t for their trajectories over time.

2
Given the time-varying parameters θ 1:T , the probability mass function observing binary sequences x0:T is given as
"
#
L Y
N
T
Y
Y
p(x0:T |θ 1:T ) =
p(xli,0 )
p(xli,t |xlt−1 , θ it ) ,
(S1.5)
l=1 i=1

t=1

where we use p(xli,0 ) = 0.5 for data generation. We assume that the same time-dependent parameters apply across
trials.
In the state-space model, the state model defines the discrete-time stochastic processes of the latent variables, which
are the time-varying parameters θ 0:T in our model. We use the following Gaussian model by assuming independent
processes across neurons:
"
#
N
T
Y
Y
i
i i
i
i
i
p(θ 0:T ) =
p(θ 0 |µ , Σ )
p(θ t |θ t−1 , Q ) ,
(S1.6)
i=1

t=1

where the transition of the i-th neuron is given by


1
1
exp − (θ it − θ it−1 )⊤ (Qi )−1 (θ it − θ it−1 )
p(θ it |θ it−1 , Qi ) = p
2
|2πQi |

(S1.7)

with Q i being the noise covariance for the transition of the i-th neuron. The initial density of the i-th neuron
p(θ i0 |µi , Σi ) is given as a Gaussian distribution with mean µi and covariance Σi . In practice, we used a zero vector
and a unit matrix before optimization, respectively. In the followings, we denote a set of hyperparameters µi , Σi , Q i
for i = 1, . . . , N collectively by w.

2.

One-step prediction density

In this section, we derive the one-step prediction density p(θ t |x0:t−1 , w), using Chapman–Kolmogorov’s equation.
For t = 1, we note that the one-step prediction is specified as a prior distribution: p(θ 1 |x0 , w) = p(θ 1 |w) =

QN
i
i
i
i=1 N θ 1 ; µ , Σ . For t = 2, . . . , T , the one-step prediction density is computed via the Chapman–Kolmogorov
equation:
Z
p(θ t |x0:t−1 , w) = p(θ t , θ t−1 |x0:t−1 , w) dθ t−1
Z
= p(θ t |θ t−1 , x0:t−1 , w) p(θ t−1 |x0:t−1 , w) dθ t−1 ,
(S1.8)
where p(θ t−1 |x0:t−1 , w) is the filter density at time t − 1. We assume that the filter density factors into a product of
individual neurons. Coupled with the factorized assumption of the state model, this leads to the factorization of the
one-step prediction density:
p(θ t |x0:t−1 , w) =

N Z
Y

i
i
i
p(θ ti |θ t−1
, w) p(θ t−1
|x0:t−1 , w) dθ t−1
.

(S1.9)

i=1
i
We further assume that the filter density at time t − 1, p(θ t−1
|x0:t−1 , w), is approximated by a Gaussian distribution
i
i
with mean θ t−1|t−1 and covariance Wt−1|t−1 (to be justified at the next filtering step):


i
i
i
i
p(θ t−1
|x0:t−1 , w) = N θ t−1
; θ t−1|t−1
, Wt−1|t−1
.

(S1.10)

Here the filter mean is defined as
θ it−1|t−1 =

Z

p(θ it−1 |x0:t−1 )θ it−1 dθ it−1 = Eθit−1 |x0:t−1 θ it−1 .

(S1.11)

It represents the expected value of the parameter at time t − 1 using data up to t − 1. The filter covariance is
i
Wt−1|t−1
= Eθit−1 |x0:t−1 (θ it−1 − Eθit−1 |x0:t−1 θ it−1 )(θ it−1 − Eθit−1 |x0:t−1 θ it−1 )⊤ .

(S1.12)

3
i
i
Given the Gaussian transition model p(θ ti |θ t−1
, w) = N (θ ti ; θ t−1
, Q i ), the one-step prediction density
p(θ t |x0:t−1 , w) becomes a Gaussian distribution. Namely, by completing the square with resect to θ ti and calculating the integral, we obtain

p(θ t |x0:t−1 , w) =

N
Y


i
i
N θ t ; θ t|t−1
, Wt|t−1
,

(S1.13)

i=1

where
i
i
θ t|t−1
= θ t−1|t−1
,

(S1.14)

i
i
Wt|t−1
= Wt−1|t−1
+ Q i.

(S1.15)

i
i
We also define θ 1|0
= µi and Wt|0
= Σi for the consistent notation of the one-step prediction density for t = 1, . . . , T
in subsequent calculations.

3.

Filtering

Using the observation model and the one-step prediction density p(θ t |x0:t−1 , w), the posterior filter density is given
as
p(θ t |x0:t , w) ∝

N Y
L
Y


exp θi,t xli,t +

i=1 l=1

N
X


θij,t xlit xlj,t−1 − ψ(θ it , xlt−1 )

j=1

N
Y



1
i
)−1 (θ it − θ it|t−1 ) .
·
exp − (θ it − θ it|t−1 )⊤ (Wt|t−1
2
i=1

(S1.16)

This expression confirms that the filter density at time t is a product of the individual neurons’ filter densities,
validating the assumption of independent filter densities in constructing the one-step prediction density. The result
enables independent filtering for each neuron.
We now approximate the filter density by the Gaussian distribution using Laplace’s method. Namely, we obtain
the maximum a posteriori (MAP) estimate of the filter density and use the Hessian at around the MAP estimate to
obtain the approximate covariance. Using
⊤

θ it = [θi,t , θi1,t , ...θiN,t ] ,

⊤
F(xli,t , xlt−1 ) = xli,t , xli,t xl1,t−1 , xli,t xl2,t−1 , . . . , xli,t xlN,t−1 ,

(S1.17)
(S1.18)

we have
p(θ t |x0:t , w) ∝

N
Y

exp

i=1

" L
X

(θ it )⊤ F(xli,t , xlt−1 ) − ψ(θ it , xlt−1 )

l=1

#
1 i
i
i
⊤
i
−1 i
− (θ t − θ t|t−1 ) (Wt|t−1 ) (θ t − θ t|t−1 ) ,
2

(S1.19)

where ψ(θ it , xlt−1 ) is now given as



ψ(θ it , xlt−1 ) = log 1 + exp (θ it )⊤ F(1, xlt−1 ) .

(S1.20)

First, we obtain the MAP estimate defined as
θ MAP = arg max log p(θ t |x0:t , w).
θt

(S1.21)

We obtain the MAP estimate through numerical optimization using the Newton-Raphson method. Notably, the MAP
estimate for each neurons, θ iMAP , can be obtained independently of the others. For this goal, we obtain the first and
second-order derivatives of the log posterior with respect to θ it . The first-order derivative with respect to θ it results in
"
#
L
i
l
∂ψ(θ
,
x
)
∂ log p(θ t |x0:t , w) X
t
t−1
i
=
F(xli,t , xlt−1 ) −
− (Wt|t−1
)−1 (θ it − θ it|t−1 ).
(S1.22)
i
∂θ it
∂θ
t
l=1

4
Here, the derivative of ψ(θ it , xlt−1 ) with respect to θ it is given by:


exp (θ it )⊤ F(1, xlt−1 )
∂ψ(θ it , xlt−1 )

 F(1, xlt−1 )
=
∂θ it
1 + exp (θ it )⊤ F(1, xlt−1 )


= exp (θ it )⊤ F(1, xlt−1 ) − ψ(θ it , xlt−1 ) F(1, xlt−1 )
l
= ri,t
(xlt−1 )F(1, xlt−1 ),

(S1.23)

where we defined the expected rate of i-th neuron at time t given the activity of the previous time step xlt−1 as
l
ri,t
(xlt−1 ) ≡ Exli,t |xlt−1 xli,t
X
p(xli,t |xlt−1 ) xli,t
=
xli,t



= exp (θ it )⊤ F(1, xlt−1 ) − ψ(θ it , xlt−1 ) .
The second derivative of log p(θ t |x0:t , w) with respect to θ it is given by
#
"

 X
L
∂ 2 ψ(θ it , xlt−1 )
∂
∂ log p(θ t |x0:t , w)
i
=
− (Wt|t−1
)−1 .
−
i
i ⊤
∂θ it
∂(θ it )⊤
∂θ
∂(θ
)
t
t
l=1

(S1.24)

(S1.25)

The second derivative of ψ(θ it , xlt−1 ) with respect to θ it is given by:
∂ 2 ψ(θ it , xlt−1 )
∂θ it (θ it )⊤



∂
exp (θ it )⊤ F(1, xlt−1 ) − ψ(θ it , xlt−1 ) F(1, xlt−1 )⊤
i
∂θ t
"
#
i
l
 i ⊤

,
x
∂ψ(θ
)
t
t−1
= exp (θ t ) F(1, xlt−1 ) − ψ(θ it , xlt−1 ) F(1, xlt−1 ) −
F(1, xlt−1 )⊤
∂θ it
=

l
l
= ri,t
(xlt−1 ){1 − ri,t
(xlt−1 )}F(1, xlt−1 )F(1, xlt−1 )⊤ .

(S1.26)

Using the first and second-order derivatives, the MAP estimate θ iMAP for each neurons was found by the NewtonRaphson method.
After finding the MAP estimate, we approximate the filter density by a Gaussian distribution via the Laplace’s
method,


1
1 i
i
i ⊤
i
−1 i
p(θ t |x1:t , w) = p
exp − (θ t − θ t|t ) Wt|t (θ t − θ t|t )
(S1.27)
2
|2πWt|t |
with the following mean and variance:
θ it|t = θ iMAP ,

(S1.28)

and
"

i

∂ log p θ t−1 |x1−t , w
∂
i
Wt|t
= − i
T
∂θ t
∂ θ it
   
−1 −1
i
= G θ it|t + Wt|t−1
,

#−1

!
θ it =θ it|t

(S1.29)


where G θ it is given by
L
 X
∂ 2 ψ(θ it , xlt−1 )
G θ it =
∂θ it ∂(θ it )⊤
l=1

=

L
X

l
l
ri,t
(xlt−1 ){1 − ri,t
(xlt−1 )}F(1, xlt−1 )F(1, xlt−1 )⊤ .

(S1.30)

l=1

By sequentially applying the one-step prediction density and the filter density for t = 1, . . . , T , we obtain the filter
densities of all time steps.

5
4.

Smoothing

Given that the filter density is approximated by Gaussian distributions, the smoothing density for the parameters of
each neuron can be computed iteratively by using the filter density and the one-step prediction density in a backward
manner from the final time step T , following the Rauch-Tung-Striebel smoother [1]:


θ it−1|T = θ it−1|t−1 + Ait−1 θ it|T − θ it|t ,
(S1.31)


⊤
i
i
i
i
(S1.32)
− Wt|t−1
Ait−1 ,
+ Ait−1 Wt|T
= Wt−1|t−1
Wt−1|T

−1
i
i
Ait−1 = Wt−1|t−1
Wt|t−1
,
(S1.33)
for t = 2, . . . , T . For completeness, we provide a compact derivation of these equations below.
At the smoothing, we estimate the latent state θ it given the entire observed data x0:T . The smoother posterior
density is given as
Z
p(θ it−1 |x0:T , w) = p(θ it−1 |θ it , x0:T , w)p(θ it |x0:T , w) dθ it
Z
= p(θ it−1 |θ it , x0:t−1 , w)p(θ it |x0:T , w) dθ it .
(S1.34)
Here, we used the Markovian assumption at the second equality. The conditional density p(θ it−1 |θ it , x0:t−1 , w) is
obtained as
p(θ it−1 |θ it , x0:t−1 , w) =
=

p(θ it−1 , θ it |x0:t−1 , w)
p(θ it |x0:t−1 , w)
p(θ it |θ it−1 , w)p(θ it−1 |x0:t−1 , w)
p(θ it |x0:t−1 , w)

,

(S1.35)

which is composed of the filter and one-step prediction densities, and the state model. Since we assume that these
are Gaussian distributions, given that the smoother density at time t is Gaussian, the linear operations in Eqs. S1.34
and S1.35 guarantee that the smoother density at time t − 1 is Gaussian. Therefore, the distribution is specified by
the mean and covariance defined as
θ it−1|T ≡ Eθit−1 |x0:T θ it−1
⊤


i
.
Wt−1|T
≡ Eθit−1 |x0:T θ it−1 − θ it−1|T
θ it−1 − θ it−1|T
To obtain their closed form expressions, first we note that the joint density in Eq. S1.35 is written as
! 
 i 
!
i
i
Wt−1|t−1
Wt−1,t|t−1
θ it−1|t−1
θ t−1
i
i
;
p(θ t−1 , θ t |x0:t−1 , w) = N
,
,
i
i
Wt,t−1|t−1
Wt|t−1
θ it
θ it|t−1

(S1.36)
(S1.37)

(S1.38)

i
where Wt−1,t|t−1
is the cross covariance given the data up to time t − 1. Here, we note that, under the linear Gaussian
transition with an identity transition matrix, the one-step prediction mean is

θ it|t−1 = θ it−1|t−1 .

(S1.39)

The cross covariance is obtained as


⊤
i
Wt−1,t|t
≡ Eθit−1 ,θit |x0:t θ it−1 − θ it−1|t−1 θ it − θ it|t−1


⊤
= Eθit−1 ,ξt |x0:t θ it−1 − θ it−1|t−1 θ it−1 + ξ t − θ it−1|t−1
h
 i
i
= Wt−1|t−1
+ Eθit−1 ,ξt |x0:t θ it−1 − θ it−1|t−1 ξ ⊤
t
i
= Wt−1|t−1
.

(S1.40)

6
Here, at the second equality, we inserted the state equation with a state noise ξ t−1 , and used θ it|t−1 = θ it−1|t−1 . The
last equality is obtained due to the orthogonality of the fluctuation of θ it−1 and noise ξt .
Given the joint density, we obtain the conditional density (Eq. S1.35). We note that given the multivariate normal
distribution,

 
  
Σaa Σab
xa
µa
,
.
(S1.41)
x=
∼N
Σba Σbb
xb
µb
The conditional distribution of xa |xb follows
xa |xb ∼ N (µa|b , Σa|b )

(S1.42)

µa|b = µa + Σab Σ−1
bb (xb − µb ),

(S1.43)

Σa|b = Σaa − Σab Σ−1
bb Σba .

(S1.44)



i
i
p(θ it−1 |θ it , x0:t−1 , w) = N θ it−1 ; θ it−1|t−1 + At−1 (θ it − θ it−1|t−1 ), Wt−1|t−1
− At−1 Wt−1|t−1
,

(S1.45)

with

Applying this formula, we obtain

i
i
where At−1 = Wt−1|t−1
(Wt|t−1
)−1 .
Finally, the smoothing density at time t is obtained by multiplying the smoother density at time t and integrating
out θ it according to Eq. S1.34. For this, we note that, given the following two normal distributions:

p(xa |xb ) = N (xa ; Axb + b, Σa|b ),
p(xb ) = N (xb ; µb , Σb ),
the marginal distribution of xa is obtained as
Z
p(xa ) = p(xa |xb ) p(xb ) dxb = N (xa ; µa , Σa ),

(S1.46)
(S1.47)

(S1.48)

where
µa = Aµb + b,

(S1.49)

⊤

Σa = AΣb A + Σa|b .
(S1.50)


i
Applying this formula to Eq. S1.45 and p(θ it |x0:T , w) = N θ it ; θ it|T , Wt|T
, we obtain the smoothing density
p(θ it−1 |x0:T , w) whose mean and covariance are given by
θ it−1|T = θ it−1|t−1 + At−1 (θ it|T − θ it−1|t−1 ),

(S1.51)

and
i
i
i
i
Wt−1|T
= At−1 Wt|T
A⊤
t−1 + Wt−1|t−1 − At−1 Wt−1|t−1
i
i
i
i
−1
i
= Wt−1|t−1
+ At−1 Wt|T
A⊤
Wt−1|t−1
t−1 − At−1 Wt|t−1 (Wt|t−1 )


i
i
i
= Wt−1|t−1
+ At−1 Wt|T
− Wt|t−1
A⊤
t−1 .

(S1.52)

We thus obtained the backward recursion formulae to obtain the smoothing densities.
5.

Optimization of hyperparameters

We consider the problem of optimizing the hyperparameters that maximize the marginal likelihood function. Instead
of the marginal likelihood, we optimize its tractable lower bound. In the Expectation-Maximization (EM) algorithm,
the posterior density is obtained under given hyperparameters via the algorithm described in the previous section

7
at the E-step. At the M-step, we optimize the hyperparameters that maximize the lower bound, using the given
posterior density. Using Jensen’s inequality log E[X] ≥ E[log X], this lower bound is given by
l(w∗ ) ≡ log p(x0:T |w∗ )
Z
p(x0:T , θ 1:T |w∗ )
= log p(θ 1:T |x0:T , w)
dθ 1:T
p(θ 1:T |x0:T , w)
p(x0:T , θ 1:T |w∗ )
= log Eθ1:T |x0:T ,w
p(θ 1:T |x0:T , w)
p(x0:T , θ 1:T |w∗ )
≥ Eθ1:T |x0:T ,w log
p(θ 1:T |x0:T , w)
= Eθ1:T |x0:T ,w log p(x0:T , θ 1:T |w∗ ) − Eθ1:T |w log p(θ 1:T |x0:T , w).

(S1.53)

The first term is called the Q-function:
Q̃(w) = Eθ1:T |x0:T ,w log p(x0:T , θ 1:T |Q)
= Eθ1:T |x0:T ,w log p(x0:T |θ 1:T , Q) + Eθ1:T |x0:T ,w log p(θ 1:T |Q).

(S1.54)

The second term is the entropy of the posterior density, which is fixed at M-step. We thus optimize the hyperparameters that maximize the Q-function. More explicitly, the Q-function can be written as
Q̃(w) = Eθ1:T |x0:T ,w

L
N X
T X
X
[(θ it )T F(xli,t , xlt−1 ) − ψ(xlt−1 )]
t=1 i=1 l=1


N 
X
1
1
− log |2πΣi | − (θ i1 − µi )⊤ (Σi )−1 (θ i1 − µi )
2
2
i=1


N
T X
X
1
1 i
i
i
⊤
i −1 i
i
− log |2πQ | − (θ t − θ t−1 ) (Q ) (θ t − θ t−1 ) .
+ Eθ1:T |x0:T ,w
2
2
t=2 i=1
+ Eθ1:T |x0:T ,w

(S1.55)

Our objective is to choose Q such that the function Q̃(Q) attains an extremum. By noting
∂ log |2πQi |
1 ∂|Qi |
1
=
=
|Qi |(Qi )−1 = (Qi )−1 ,
i
i
i
∂Q
|Q | ∂Q
|Qi |

(S1.56)

and
∂
∂(Qi )−1
∂
i
i
i
⊤
i −1 i
(θ
−
θ
)
(Q
)
(θ
−
θ
)
=
(θ i − θ it−1 )⊤ (Qi )−1 (θ it − θ it−1 )
t
t−1
t
t−1
∂Qi
∂Qi ∂(Qi )−1 t
= −(Qi )−2 (θ it − θ it−1 )(θ it − θ it−1 )⊤ ,

(S1.57)

we obtain

T 
X
∂ Q̃(w)
1 i −1 1 i −2 i
i
i
i
⊤
= Eθ1:T |x1:T ,w
− (Q ) + (Q ) (θ t − θ t−1 )(θ t − θ t−1 ) .
∂Qi
2
2
t=2

(S1.58)

Setting the above derivative equal to zero, it follows that the optimal Qi is obtained as
Qi =

T
1 X
Eθ |x ,w (θ it − θ it−1 )(θ it − θ it−1 )⊤ .
T − 1 t=2 1:T 1:T

We note that the expectation in the above equation can be decomposed into


Eθ1:T |x1:T ,w θ it (θ it )⊤ − θ it−1 (θ it )⊤ − θ it (θ it−1 )⊤ + θ it−1 (θ it−1 )⊤ .

(S1.59)

(S1.60)

Hence, using the following definitions of the equal-time covariance matrix:
i
Wt|T
= Eθ1:T |x0:T ,w θ it (θ it )⊤ − θ it|T (θ it|T )⊤ ,

(S1.61)

8
and the delayed covariance:
i
Wt,t−1|T
= Eθ1:T |x0:T ,w (θ it − θ it|T )(θ it−1 − θ it−1|T )⊤

= Eθ1:T |x0:T ,w θ it (θ it−1 )⊤ − θ it|T (θ it−1|T )⊤ ,

(S1.62)

the optimal Qi is obtained as
Qi =

T
i
1 Xh i
i
i
i
i
(θ t|T − θ it−1|T )(θ it|T − θ it−1|T )⊤ + Wt|T
− Wt−1,t|T
− Wt,t−1|T
+ Wt−1|T
,
T − 1 t=2

(S1.63)

i
i
where Wt−1,t|T
= (Wt,t−1|T
)⊤ . We compute the lag-one smoothed covariance following the method of De Jong and
Mackinnon [2]:
i
i
i
i
= Wt|t
(Wt+1|t
)−1 Wt|T
.
Wt,t−1|T

(S1.64)

i
Σi = W1|T
+ (θ i1|T − µ)(θ i1|T − µ)⊤ .

(S1.65)

Similarly, we update Σi according to

6.

Approximate log marginal likelihood function

The convergence of the EM algorithm was assessed using the log marginal likelihood. Below, we derive the approximate solution for the log marginal likelihood of the kinetic Ising model.
First, we note that the marginal likelihood function p(x0:T |w) can be expressed as follows:
p(x0:T |w) = p(x0 )

T
Y

p(xt |x0:t−1 , w)

t=1

= p(x0 )

T Z
Y

dθ t p(xt |x0:t−1 , θ t , w)p(θ t |x0:t−1 , w)

t=1

= p(x0 )

T Z
Y

dθ t p(xt |xt−1 , θ t )p(θ t |x0:t−1 , w)

t=1

= p(x0 )

T Y
N Z
Y

dθ it

t=1 i=1

L
Y

p(xli,t |xt−1 , θ it )p(θ it |x0:t−1 , w).

(S1.66)

l=1

The observation model and the one-step prediction density in the equation above are written as


L
L
N
Y
Y
X
p(xli,t |xlt−1 , θ it ) =
exp θi,t xli,t +
θij,t xlit xlj,t−1 − ψ(θ it , xlt−1 )
l=1

j=1

l=1

"
= exp

(θ it )T

L
X
l=1

F(xli,t , xlt−1 ) −

L
X

#
ψ(θ it , xlt−1 )

,

(S1.67)

l=1

and
p(θ it |x0:t−1 , w) = q

1
i
|2πWt|t−1



1 i
i
i
−1 i
⊤
i
exp − (θ t − θ t|t−1 ) (Wt|t−1 ) (θ t − θ t|t−1 ) .
2
|

Substituting Eqs.S1.67 and S1.68 into Eq.S1.66, we obtain
N Y
T Z
Y
1
p(x0:T |w) = p(x0 )
dθ it q
i
|2πWt|t−1
|
i=1 t=1
"
#
L
L
X
X
1
i
· exp (θ it )T
F(xli,t , xlt−1 ) −
ψ(θ it , xlt−1 ) − (θ it − θ it|t−1 )⊤ (Wt|t−1
)−1 (θ it − θ it|t−1 ) .
2
l=1

l=1

(S1.68)

(S1.69)

9
We now define the function q(θ it ) as follows:
q(θ it ) = (θ it )T

L
X

F(xli,t , xlt−1 ) −

l=1

L
X
l=1

1
i
)−1 (θ it − θ it|t−1 ).
ψ(θ it , xlt−1 ) − (θ it − θ it|t−1 )⊤ (Wt|t−1
2

(S1.70)

The Taylor expansion of q(θ it ) around θ ∗ up to the second order yields
q(θ it ) = q(θ ∗ ) +

1 i
∂ 2 q(θ i )
∂q(θ it )
i
∗
∗ ⊤
(θ
−
θ
)
+
(θ it − θ ∗ ).
(θ
−
θ
)
t
2 t
∂θ it θi =θ∗
∂θ it ∂(θ it )⊤ θi =θ∗
t

(S1.71)

t

The value of θ it that maximizes the function q(θ it ) is the MAP estimate θ it|t of the filter density. Further, the quadratic
i
term evaluated at the MAP estimate is given by the negative inverse of the filter covariance Wt|t
. Hence, at θ ∗ = θ it|t ,
the Taylor expansion becomes
1
i −1 i
q(θ it ) ≃ q(θ it|t ) − (θ it − θ it|t )⊤ (Wt|t
) (θ t − θ it|t ).
2

(S1.72)

With this quadratic approximation, the marginal likelihood is obtained as
p(x0:T |w) ≃ p(x0 )

N Z
T Y
Y

dθ it q

1



i
i
i ⊤1
i
i −1 i
exp q(θ t|t ) − (θ t − θ t|t ) [Wt|t ] (θ t − θ t|t )
2
|

i
|2πWt|t−1
q
i |


Z
N
T Y
|2πWt|t
Y
1
i ⊤1
i
i
i
i
i −1 i
q
exp[q(θ t|t )] q
dθ t exp −(θ t − θ t|t ) [Wt|t ] (θ t − θ t|t )
= p(x0 )
i
i |
2
|2πWt|t−1
| |2πWt|t
t=1 i=1
v
T Y
N u
i |
Y
u |2πWt|t
t
= p(x0 )
exp[q(θ it|t )].
(S1.73)
i
|2πW
|
t|t−1
t=1 i=1
t=1 i=1

We thus obtain the log marginal likelihood function as follows:
log p(x0:T |w) ≃ log p(x0 ) +

T X
N 
X
1
t=1 i=1

2

i
log |Wt|t
|−


1
i
log |Wt|t−1
| + q(θ it|t ) .
2

(S1.74)

10
Supplementary Note 2: An alternative calculation of the backward conditional entropy

Here, we give an alternative approach to obtaining the backward conditional entropy to the one given in Methods.
The result gives an identical approximate solution.
Under the approximation of the following probabilities by independent distributions:
p(xt−2 ) = Q(xt−2 ),
p(xt |xt−1 ) = Q(xt ),

(S2.1)
(S2.2)

the backward conditional entropy is approximated as
X
X
X X
σtbackward = −
p(xt−1 |xt−2 )p(xt−2 )
p(xt |xt−1 )
[xi,t−1 hi,t (xt ) − ψ(hi,t (xt ))]
≃−

xt−2 xt−1

xt

X X

X

p(xt−1 |xt−2 )Q(xt−2 )

xt−2 xt−1

=−

Q(xt )

xt

X X X
i

i

X

p(xi,t−1 |xt−2 )Q(xt−2 )

[xi,t−1 hi,t (xt ) − ψ(hi,t (xt ))]

i

X

xi,t−1 xt−2

Q(xt ) [xi,t−1 hi,t (xt ) − ψ(hi,t (xt ))] .

(S2.3)

xt

Let us define ϕ̃i,t (xi,t ) as
ϕ̃i,t (xi,t−1 ) =

X

Q(xt ) [xi,t−1 hi,t (xt ) − ψ(hi,t (xt ))] .

(S2.4)

xt

Using
γ(hi,t ) = xi,t−1 hi,t − ψ(hi,t ),

(S2.5)

we approximate ϕ̃i,t (xi,t ) as
Z
ϕ̃i,t (xi,t−1 ) ≈

Dz γ(gi,t + z

p
∆i,t ),

(S2.6)


where Dz = √dz
exp − 12 z 2 .
2π
Then, the backward conditional entropy is written as
X X
σtbackward = −
p(xt−1 |xt−2 )Q(xt−2 )ϕ̃i,t (xi,t−1 )
xt−2 xt−1


=−

X X


X


i

xi,t−1

p(xi,t−1 |xt−2 )Q(xt−2 ) ϕ̃i,t (xi,t−1 ).

(S2.7)

xt−2

Note that, from Eq. 51, we have
mi,t =

X

p(xt = 1|xt−1 )p(xt−1 ) ≃

xt−1

1 − mi,t =

X
xt−1

X

p(xt = 1|xt−1 )Q(xt−1 ),

xt−1

p(xt = 0|xt−1 )p(xt−1 ) ≃

X

p(xt = 0|xt−1 )Q(xt−1 ).

(S2.8)

xt−1

Applying these equations for the case of t − 1, we obtain
o
Xn
σtbackward ≃ −
mi,t−1 ϕ̃i,t (xi,t−1 = 1) + (1 − mi,t−1 )ϕ̃i,t (xi,t−1 = 0) .

(S2.9)

i

Thus, it can be obtained by computing the two Gaussian integral terms.
Since this equation can be further computed as
o
Xn
σtbackward ≃ −
mi,t−1 (ϕ̃i,t (xi,t−1 = 1) − ϕ̃i,t (xi,t−1 = 0)) + ϕ̃i,t (xi,t−1 = 0) .
i

(S2.10)

11
and
ϕ̃i,t (xi,t−1 = 1) − ϕ̃i,t (xi,t−1 = 0) =

X

Q (xt ) hi,t (xt ),

xt

ϕ̃i,t (xi,t−1 = 0) = −

X

Q (xt ) ψ(hi,t (xt )),

(S2.11)

Q(xt ) [mi,t−1 hi,t (xt ) − ψ(hi,t (xt ))] ,

(S2.12)

xt

it becomes
σtbackward = −

XX
i

xt

which is equivalent to Eq. 56 in Methods and can be also approximated by the Gaussian integral.

12
Supplementary Note 3: Mean-field entropy flow under specific conditions

In this section, we derive the mean-field approximation of the entropy flow under the steady-state conditions or for
independent neurons.
First, let us summarize the mean-field entropy flow. It is obtained as
σtflow = −σtforward + σtbackward


i
h

XZ
p
p
≈
Dz −χ gi,t,t−1 + z ∆i,t,t−1 + ϕi,t gi,t,t + z ∆i,t,t ,

(S3.1)

i

where gi,t,s and ∆i,t,s (s = t, t − 1) are given as
gi,t,s = θi,t +

X

θij,t mj,s ,

(S3.2)

2
θij,t
mj,s (1 − mj,s ).

(S3.3)

j

∆i,t,s =

X
j

Here mj,s is the mean-field activation rate of the j-th neuron at time s.
Using r(h) = 1/(1 + e−h ) and ψ(h) = − log(1 − r(h)), χ(h) and ϕi,t (h) are given as
χ(h) = −r(h) log r(h) − (1 − r(h)) log(1 − r(h))
r(h)
− log(1 − r(h))
= −r(h) log
1 − r(h)
= −r(h)h + ψ(h),

(S3.4)

ϕi,t (h) = −mi,t−1 h + ψ(h).

(S3.5)

and

1.

Steady-state solution

Under the steady-state assumption (mi,t = mi,t−1 ≡ mi ), we have gi,t,t−1 = gi,t,t ≡ gi and ∆i,t,t−1 = ∆i,t,t ≡ ∆i ,
making
√ the inputs to χ and ϕi,t common for each neuron. Then, using Eqs. S3.4 and S3.5 with the common h =
gi + z ∆i , we have
 
 
XZ
p 
p 
σtflow ≈
Dz r gi + z ∆i − mi · gi + z ∆i
i

=

XZ

Dz

 
 p
p 
r gi + z ∆i − mi · z ∆i .

(S3.6)

i

√ 
The term r gi + z ∆i − mi represents how the neuron’s activity rate deviates from its long-term average, while
√
z ∆i is the fluctuating input to that neuron. Thus, the mean-field solution for the steady state provides an intuitive
picture of entropy flow as a measure of the neuron’s causal response to fluctuations in its input.
The non-negativity of the mean-field entropy flow can be formally confirmed by Stein’s lemma E(f (X)(X − µ)) =
σ 2 E(f ′ (X))
random variable X with expectation µ and variance σ 2 . By identifying f (h) = r(h) − mi ,
√ for a Gaussian
′
h − gi = z ∆i , and f (h) = r′ (h), it can be written as

X Z
p
flow
′
σt ≈
∆i
Dz r (gi + z ∆i ) ,
(S3.7)
i

where r′ (h) = r(h)(1 − r(h)). Since ∆i ≥ 0 and r′ (h) ≥ 0, the entropy flow is non-negative, which satisfies the
requested property of the entropy flow at the steady state. However, while insightful, this form also reveals a key
limitation of the approximation: the zero entropy flow is realized only at θij = 0 (except for r = 0, 1). Consequently,
it does not correctly reduce to zero for symmetric couplings, failing to fully incorporate the distinction between
symmetric and asymmetric interactions.

13
2.

Independent neurons

Here we consider independent neurons (i.e., no couplings θij = 0) with time-varying field θi,t . The entropy flow in
this system is caused solely by the time-varying fields, or equivalently, the activity rate of individual neurons.
In this case, we have
gi,t,s = θi,t ,
∆i,t,s = 0,

(S3.8)
(S3.9)

which is independent of s, making the inputs to χ and ϕi,t common once again. Then, we have
X
σtflow ≈
(r (θi,t ) − mi,t−1 ) · θi,t
i

=

X

(mi,t − mi,t−1 ) · θi,t .

(S3.10)

i

For θi,t < 0, which corresponds to mi,t < 0.5, a decrease in the activity rate mi,t − mi,t−1 < 0 yields positive entropy
flow, and an increase in the activity rate induces negative entropy flow.

14
Supplementary Note 4: The d-prime measure

Here, we provide the definition of the primary behavioral metric, d′ (d-prime), for clarity. This follows the white
paper of “Allen Brain Observatory: Visual Behavior Neuropixels”, where further details are available.
To evaluate the sensitivity of the mice to the stimulus, the primary behavioral metric, d′ , was calculated using data
detected only in the active condition with visual changes. The formula for d′ is as follows:
d′ = Z(RH ) − Z(RF ),

(S4.1)

where RH is the hit rate (the proportion of trials in which the mouse correctly responded to a change in the visual
stimulus), and RF is the false alarm rate (the proportion of trials in which the mouse incorrectly responded to a
non-existent change). The function Z represents the inverse of the cumulative distribution function of a standard
normal distribution, converting the hit and false alarm rates into z-scores. To prevent extreme values (e.g., 0 or 1)
from distorting the results, RH and RF were adjusted using the following boundary equations:
1
1
≤ RH ≤ 1 −
,
2NH
2NH

1
1
≤ RF ≤ 1 −
,
2NF
2NF

(S4.2)

where NH and NF are the total number of trials for the hit and false alarm conditions, respectively. To assess the
overall behavioral performance across sessions or experimental conditions, mean d′ was used as an aggregated measure,
representing the average d′ over multiple trials or sessions. For more details, see [3].

15
Supplementary Note 5: Entropy flow of high-firing neurons and behavioral performance

To elucidate how individual neurons increase total entropy flow in the active condition despite a smaller fraction of
neurons exhibiting substantial firing rates (Supplementary Fig. S2, Fig. S3, and Fig. S4), we examined the relationship
between the entropy flow and spike rates of individual neurons.
As shown in Eqs. 13 and 14, the mean-field entropy flow can be decomposed into contributions from individual
neurons. We computed the entropy flow of individual neurons under the active and passive conditions and compared
them with their firing rates (Supplementary Fig. S8A, mouse 574078). The dotted lines connect the values for the
active (red) and passive (blue) conditions. We then investigated whether the change in the entropy flow by the
behavioral conditions depends on the neuron’s firing rate. Supplementary Fig. S8B shows the relationship between
the geometric mean spike rates of the two conditions (abscissa) and the difference in entropy flow (ordinate) for
individual neurons. The difference was computed as ‘active’ - ‘passive,’ indicating that the positive value marks a
larger entropy flow in the active condition. The positive Spearman rank correlation coefficient (ρ = 0.22) for this
exemplary mouse suggests that neurons with higher spike rates contributed to increasing total entropy flow in the
active condition, despite the summed entropy flow differences across all individual neurons being negative (−3.8331
for this mouse). However, significant variations in the rank correlations were observed across mice.
Assuming that fewer high-firing neurons in the sparsely active populations in the active condition play a critical
role in sensory processing (i.e., sparse coding [4–6]) and that such sensory processing involves time-asymmetric causal
patterns, we hypothesized that the above relationship between the spike rates and entropy flow change might be related
to mice’s cognitive performance. To evaluate the task sensitivity of the mice, we used the primary behavioral metric,
d′ (mean d-prime, see Supplementary Note 4 for its definition). The scatter plot in the left panel of Supplementary
Fig. S8C illustrates the relationship between behavioral measures (mean d-prime) and the rank correlation of entropy
flow change with spike rates for all mice for image ’im036 r’. The plot suggests a positive dependency between these
two values (ρ = 0.3578 measured by the Spearman rank correlation). To confirm this result, we conducted the
permutation test that compared the observed rank correlation of the scatter plot with those of the surrogate data
constructed by permuting the values of mean d-prime (Supplementary Fig. S8C Right). The result confirms the
statistical significance of the positive correlation (p = 0.0304).
To corroborate that the result does not reflect estimation error in couplings, we analyzed trial-shuffled data, which
showed no clear trend (Supplementary Fig. S8D). A permutation test confirmed that the observed correlation yielded
a non-significant p-value of 0.5063. This result confirms that the association between higher entropy flow and higher
firing neurons in more task-sensitive mice was driven by significant changes in the coupling strengths between the
active and passive conditions, rather than firing rate shifts or noise couplings.
However, the additional analyses on the images im012 r and im115 r revealed that these relations were not significantly correlated (‘im012 r’: p = 0.574; ‘im115 r’: p = 0.333, permutation test). Similar analysis replacing the
difference of the entropy flow between active and passive conditions with the difference of the entropy flow per activity
rate between active and passive conditions yielded non-significant results for these three images.

16
REFERENCES
[1] Rauch, H. E., Tung, F. & Striebel, C. T. Maximum likelihood estimates of linear dynamic systems. AIAA journal 3,
1445–1450 (1965).
[2] Jong, P. D. & Mackinnon, M. J. Covariances for smoothed estimates in state space models. Biometrika 75, 601–602 (1988).
[3] Hautus, M. J., Macmillan, N. A. & Creelman, C. D. Detection theory: A user’s guide (Routledge, 2021).
[4] Olshausen, B. A. & Field, D. J. Emergence of simple-cell receptive field properties by learning a sparse code for natural
images. Nature 381, 607–609 (1996).
[5] Olshausen, B. A. & Field, D. J. Sparse coding with an overcomplete basis set: A strategy employed by v1? Vision research
37, 3311–3325 (1997).
[6] Foldiak, P. Sparse coding in the primate cortex. The handbook of brain theory and neural networks 895–898 (2003).

Supplementary Fig. S1. Estimated neural dynamics under active and passive conditions in shuffled data of
mouse 574078. Presentation style follows Fig. 6.

Mouse 570299 - Familiar - G - im036_r
Spikes: T=75, R=593, N=240

0.01

80
60
40

0.1

0.2

0.3

0.4
Time [s]

0.5

0.6

0

0.7

0.4
Time [s]

0.5

0.6

5

Active Behavior
Passive Replay

20 25
Spike Rate

30

35

40

45

0.2

0.3

0.4
Time [s]

0.5

0.6

30
20

0

5

10

15

20 25
Spike Rate

30

35

40

45

0

5

10

15

20 25
Spike Rate

30

35

40

45

20

0.4
Time [s]

0.5

0.6

0

0.7

Mouse 509808 - Familiar - G - im036_r
Spikes: T=75, R=609, N=69
0.10

0.04

0

5

10

15

20 25
Spike Rate

30

35

40

0.2

0.3

0.4
Time [s]

0.5

0.6

0.7

0.3

0.4
Time [s]

0.5

0.6

45

20
15

0.00
0.0

0.1

0.2

0.3

0.4
Time [s]

0.5

0.6

15

20 25
Spike Rate

30

35

40

0.2

0.3

0.4
Time [s]

0.5

0.6

5

15

20 25
Spike Rate

30

35

40

45

0.02

0.2

0.3

0.4
Time [s]

0.5

0.6

0

5

10

15

20 25
Spike Rate

30

35

40

45

20
15

0.06
0.04
0.03
0.02

0.1

0.2

0.3

0.4
Time [s]

0.5

0.6

0.7

15

20 25
Spike Rate

30

35

40

45

Active Behavior
(CV=1.48)
Passive Replay
(CV=1.27)

50
40
30
10

0.2

0.3

0.4
Time [s]

0.5

0.6

0

0.7

Mouse 554013 - Familiar - G - im036_r
Spikes: T=75, R=556, N=161

0.04
0.03

0

5

10

15

20 25
Spike Rate

30

35

40

45

Mouse 554013 - Familiar - G - im036_r
Spike Rate Dist.

100

Active Behavior
Passive Replay

0.05

Active Behavior
(CV=1.84)
Passive Replay
(CV=1.47)

80
60
40
20

0.1

0.2

0.3

0.4
Time [s]

0.5

0.6

0

0.7

0

5

10

15

20 25
Spike Rate

30

0.04

40

45

Active Behavior
(CV=1.38)
Passive Replay
(CV=1.32)

70
60

0.06

35

Mouse 577287 - Familiar - G - im036_r
Spike Rate Dist.

80

Active Behavior
Passive Replay

0.08

50
40
30
20

0.02

10
0

5

10

15

20 25
Spike Rate

30

35

40

45

0.00
0.0

Active Behavior
(CV=1.53)
Passive Replay
(CV=1.28)

40
30
20

0.1

0.2

0.3

0.4
Time [s]

0.5

0.6

0

0.7

Mouse 544838 - Familiar - G - im036_r
Spikes: T=75, R=632, N=134

0

5

10

15

20 25
Spike Rate

30

0.04

40

45

Active Behavior
(CV=1.61)
Passive Replay
(CV=1.34)

70
60

0.06

35

Mouse 544838 - Familiar - G - im036_r
Spike Rate Dist.

80

Active Behavior
Passive Replay

0.08

50
40
30
20

0.02

10
0

5

10

15

20 25
Spike Rate

30

35

40

45

0.00
0.0

Mouse 521466 - Familiar - G - im036_r
Spike Rate Dist.

0.05

10

Mouse 599294 - Familiar - G - im036_r
Spike Rate Dist.

20

0.1

0.06

0.00
0.0

5

60

Mouse 577287 - Familiar - G - im036_r
Spikes: T=75, R=586, N=170

Active Behavior
(CV=1.55)
Passive Replay
(CV=1.18)

25

0

Active Behavior
Passive Replay

0.07

0.00
0.0

0

70

0.02

Mouse 541234 - Familiar - G - im036_r
Spike Rate Dist.

60

0.7

0

0.7

Active Behavior
Passive Replay

0.07

10
0.1

0.6

0.03

0.01

50

0.03

0.5

0.04

Mouse 533537 - Familiar - G - im036_r
Spike Rate Dist.

0.04

0.4
Time [s]

0.05

0.08

Active Behavior
(CV=1.64)
Passive Replay
(CV=1.32)

Mouse 521466 - Familiar - G - im036_r
Spikes: T=75, R=533, N=196

45

10

30

Active Behavior
Passive Replay

0.3

0.06

0.02

0

0.2

0.07

Mouse 560356 - Familiar - G - im036_r
Spike Rate Dist.

35

0.7

20
0.1

Mouse 599294 - Familiar - G - im036_r
Spikes: T=75, R=539, N=144

10

5
0.1

0.00
0.0

20

0.02

Neuron Count

Spike Probability
0

30

10

0.00
0.0

45

0.01

40

0.04

0.00
0.0

40

50

0

Active Behavior
Passive Replay

0.06

0.00
0.0

35

40

70

0.7

0.08

0

10

30

60

0.10

0.01
5

20 25
Spike Rate

Active Behavior
(CV=1.64)
Passive Replay
(CV=1.54)

80

Active Behavior
Passive Replay

0.04

5
0

15

60

0

0.7

0.05

Active Behavior
(CV=1.60)
Passive Replay
(CV=1.04)

25

10

0.02

0.2

0.06

Mouse 509808 - Familiar - G - im036_r
Spike Rate Dist.

30
Neuron Count

0.06

0.1

0.01

35

Active Behavior
Passive Replay

0.08

0.1

0.00
0.0

0.06

Spike Probability

0.3

10

80

Mouse 533537 - Familiar - G - im036_r
Spikes: T=75, R=468, N=126

Spike Probability

30

5

20

0.12

10

0.02
0.2

0.03

0.14

Active Behavior
(CV=1.61)
Passive Replay
(CV=1.20)

40
Neuron Count

0.04

0.1

0.04

Mouse 553960 - Familiar - G - im036_r
Spike Rate Dist.

0.06

Active Behavior
Passive Replay

Mouse 541234 - Familiar - G - im036_r
Spikes: T=75, R=621, N=42

Spike Probability

40

0

Mouse 524925 - Familiar - G - im036_r
Spike Rate Dist.

0.08

Active Behavior
(CV=1.54)
Passive Replay
(CV=1.35)

Mouse 553960 - Familiar - G - im036_r
Spikes: T=75, R=598, N=74
Active Behavior
Passive Replay

0

0.7

0.02

60

0

0.7

0.6

0.05

0.10

20
0.1

0.5

Mouse 560356 - Familiar - G - im036_r
Spikes: T=75, R=572, N=166

Active Behavior
(CV=1.64)
Passive Replay
(CV=1.18)

80
Neuron Count

0.04

0.08
Spike Probability

15

Spike Probability

Spike Probability
Spike Probability

0.06

0.4
Time [s]

0.06

Mouse 560771 - Familiar - G - im036_r
Spike Rate Dist.

0.02

Spike Probability

10

40

0

0.7

0.3

0.01
0

50
Neuron Count

0.3

0.2

0.07

10
0.2

0.1

0.08

Mouse 574081 - Familiar - G - im036_r
Spike Rate Dist.

Active Behavior
Passive Replay

0.1

0.00
0.0

Mouse 524925 - Familiar - G - im036_r
Spikes: T=75, R=584, N=164

20

0.08

0.00
0.0

45

0.02

Mouse 560771 - Familiar - G - im036_r
Spikes: T=75, R=591, N=171

0.00
0.0

40

Active Behavior
(CV=1.74)
Passive Replay
(CV=1.58)

Mouse 574081 - Familiar - G - im036_r
Spikes: T=75, R=580, N=124

0.10

35

Spike Probability

0.02

0.00
0.0

30

120
Neuron Count

Spike Probability

0.03

0.08
0.07
0.06
0.05
0.04
0.03
0.02
0.01
0.00
0.0

20 25
Spike Rate

100

0.04

0.00
0.0

15

Mouse 570299 - Familiar - G - im036_r
Spike Rate Dist.

Active Behavior
Passive Replay

0.05

10

40

Neuron Count

5

60

Neuron Count

0

0.04

Neuron Count

0

0.7

0.06

Neuron Count

0.6

Spike Probability

0.5

Spike Probability

0.4
Time [s]

80

0.02

Spike Probability

0.3

20

0.01

Neuron Count

0.2

40

Active Behavior
(CV=1.58)
Passive Replay
(CV=1.40)

100

80
60
40

20 25
Spike Rate

30

35

40

0.6

0

0.7

0.02

45

0

5

10

15

20 25
Spike Rate

30

35

40

45

Mouse 530862 - Familiar - G - im036_r
Spike Rate Dist.

35

Active Behavior
Passive Replay

0.03

0.00
0.0

15

0.5

0.04

0

10

0.4
Time [s]

Active Behavior
(CV=1.12)
Passive Replay
(CV=1.28)

30

0.05

0.01
5

0.3

0.06

20
0

0.2

Mouse 530862 - Familiar - G - im036_r
Spikes: T=75, R=599, N=71

Active Behavior
(CV=1.60)
Passive Replay
(CV=1.35)

100

0.1

Neuron Count

0.02

20
0.1

0.03

Neuron Count

0.00
0.0

0.04

Neuron Count

0.02

0.05

60

Spike Probability

40

0.06

Mouse 532246 - Familiar - G - im036_r
Spike Rate Dist.

Active Behavior
Passive Replay

0.08

Spike Probability

60

Mouse 532246 - Familiar - G - im036_r
Spikes: T=75, R=581, N=210

Active Behavior
(CV=1.86)
Passive Replay
(CV=1.35)

80

Neuron Count

0.04

Active Behavior
Passive Replay

0.07
Spike Probability

Neuron Count

Spike Probability

80
0.06

0.08

Active Behavior
(CV=1.51)
Passive Replay
(CV=1.27)

Neuron Count

0.08

(1 to 18 mice)

Familiar G im036_r Mouse 536480 - Familiar - G - im036_r
Mouse 536480 - Familiar - G - im036_r
Spikes: T=75, R=612, N=159
Spike Rate Dist.

Mouse 574078 - Familiar - G - im036_r
Spike Rate Dist.
100

Active Behavior
Passive Replay

Neuron Count

Mouse 574078 - Familiar - G - im036_r
Spikes: T=75, R=589, N=212

25
20
15
10
5

0.1

0.2

0.3

0.4
Time [s]

0.5

0.6

0.7

0

0

5

10

15

20 25
Spike Rate

30

35

40

45

Supplementary Fig. S2. Spike-rate dynamics and distributions for mice 1-18. Spike-rate dynamics and distributions
under the active (red) and passive (blue) conditions. The presentation styles for each mouse follow Fig. 6A. The mice were
listed in descending order of behavioral performance measured by d-prime. See Supplementary Fig. S3 for the remaining mice.

0.04
0.02
0.2

0.3

0.4
Time [s]

0.5

0.6

0.7

80
70
60
50
40
30
20
10
0

Active Behavior
Passive Replay

0.4
Time [s]

0.5

0.6

0

5

0.2

0.3

0.4
Time [s]

0.5

0.6

0

5

Active Behavior
Passive Replay

40

45

20 25
Spike Rate

30

35

40

40
30

45

0.03

0.2

0.3

0.4
Time [s]

0.5

0.6

0.00
0.0

0.7

Active Behavior
Passive Replay

0.05
0.04
0.03
0.02

0.3

0.4
Time [s]

0.5

0.6

0

5

10

15

20 25
Spike Rate

30

35

40

45

Mouse 548721 - Familiar - G - im036_r
Spikes: T=75, R=473, N=179

0

5

10

15

20 25
Spike Rate

30

0.1

0.2

0.3

0.4
Time [s]

0.5

0.03
0.02

0.6

20 25
Spike Rate

30

35

40

40

0

0

5

10

15

20 25
Spike Rate

30

45

0.04
0.03

0.00
0.0

0.1

0.2

0.3

0.4
Time [s]

0.5

0.6

35

40

50
40
30

0

0.7

35

40

45

30

0.04
0.03

5

10

15

20 25
Spike Rate

30

35

40

0.00
0.0

0.1

0.2

0.3

0.4
Time [s]

0.5

0.6

15

20 25
Spike Rate

30

35

40

45

40

5

10

15

20 25
Spike Rate

30

35

40

0.04
0.03

0.00
0.0

Active Behavior
Passive Replay

0.04

0.2

0.3

0.4
Time [s]

0.5

0.6

0.7

60
50
40
30

0

0.4
Time [s]

0.5

0.6

0.03
0.02

0.2

0.3

0.4
Time [s]

0.5

0.6

5

10

15

20 25
Spike Rate

30

35

40

0

5

15

20 25
Spike Rate

30

35

40

45

Active Behavior
(CV=1.35)
Passive Replay
(CV=1.11)

50
40
30
20
0

Active Behavior
Passive Replay

0.04
0.03

0

5

10

15

20 25
Spike Rate

30

35

40

45

Active Behavior
(CV=1.36)
Passive Replay
(CV=1.36)

80
60
40
20

0.1

0.2

0.3

0.4
Time [s]

0.5

0.6

0

0.7

0.04

0

5

10

15

20 25
Spike Rate

30

35

40

45

Mouse 578257 - Familiar - G - im036_r
Spike Rate Dist.

70

Active Behavior
Passive Replay

0.06

Active Behavior
(CV=1.49)
Passive Replay
(CV=1.31)

60
50
40
30
20
10

0.1

0.2

0.3

0.4
Time [s]

0.5

0.10

0.6

0

0.7

0

5

10

15

20 25
Spike Rate

30

35

40

45

Mouse 556014 - Familiar - G - im036_r
Spike Rate Dist.

Active Behavior
Passive Replay

Active Behavior
(CV=1.16)
Passive Replay
(CV=1.00)

25

0.08

20

0.06
0.04

0.00
0.0

10

Mouse 548720 - Familiar - G - im036_r
Spike Rate Dist.

Mouse 556014 - Familiar - G - im036_r
Spikes: T=75, R=581, N=57

45

45

Mouse 553253 - Familiar - G - im036_r
Spike Rate Dist.

0.02
0

40

40

60

0.7

0.05

0.00
0.0

35

10
0.1

0.08

45

30

Active Behavior
(CV=1.37)
Passive Replay
(CV=1.35)

70

Active Behavior
Passive Replay

0.04

0.00
0.0

20 25
Spike Rate

60

0

0.7

Mouse 578257 - Familiar - G - im036_r
Spikes: T=75, R=356, N=139

10
0.1

0.3

0.06

Active Behavior
(CV=1.46)
Passive Replay
(CV=1.12)

70

20

0.00
0.0

0.2

0.07

45

15

20
0.1

0.05

0.00
0.0

10

80

0.02

Mouse 524761 - Familiar - G - im036_r
Spike Rate Dist.

0.06

5

Mouse 544836 - Familiar - G - im036_r
Spike Rate Dist.

0.02
0

0

Mouse 553253 - Familiar - G - im036_r
Spikes: T=75, R=615, N=240

Active Behavior
(CV=1.90)
Passive Replay
(CV=1.32)

60

0

0.7

0

0.7

Active Behavior
Passive Replay

0.06

20

0.08

45

10

100

0.02

0.02
0

5

Mouse 524761 - Familiar - G - im036_r
Spikes: T=75, R=532, N=145

Spike Probability

40

0

80

0.05

0.6

0.05

Mouse 567286 - Familiar - G - im036_r
Spike Rate Dist.

Active Behavior
Passive Replay

0.06

0.5

Mouse 548720 - Familiar - G - im036_r
Spikes: T=75, R=514, N=137

Active Behavior
(CV=1.35)
Passive Replay
(CV=1.13)

70
60

0.05

0.4
Time [s]

0.01

80

Active Behavior
Passive Replay

0.3

0.06

Mouse 555304 - Familiar - G - im036_r
Spike Rate Dist.

0.06

0.2

0.07

Active Behavior
(CV=1.53)
Passive Replay
(CV=1.33)

60

0.7

Neuron Count

Spike Probability
15

80

Mouse 555304 - Familiar - G - im036_r
Spikes: T=75, R=595, N=194

0.07

Active Behavior
(CV=1.52)
Passive Replay
(CV=1.28)

15
10
5

0.1

0.2

0.3

0.4
Time [s]

0.5

0.6

0.7

0

0

5

10

15

20 25
Spike Rate

30

35

40

45

Mouse 548721 - Familiar - G - im036_r
Spike Rate Dist.
Active Behavior
(CV=1.78)
Passive Replay
(CV=1.54)

80
Neuron Count

0.04

10

100

0.01

100

Active Behavior
Passive Replay

0.05

5

40
20

0.1

0.01

Mouse 567286 - Familiar - G - im036_r
Spikes: T=75, R=475, N=178

Active Behavior
(CV=1.55)
Passive Replay
(CV=1.38)

50

0

0.7

Active Behavior
(CV=1.80)
Passive Replay
(CV=1.17)

0

Active Behavior
(CV=1.67)
Passive Replay
(CV=1.32)

60

Mouse 544836 - Familiar - G - im036_r
Spikes: T=75, R=564, N=201

20

0.00
0.0

0.00
0.0

Mouse 568963 - Familiar - G - im036_r
Spike Rate Dist.

10
0.2

45

0.01

20

0.1

40

0.02

70

0.01

0.6

35

10

80

Neuron Count

0.02

0.5

30

20

60

0.03

0.4
Time [s]

80
70
60
50
40
30
20
10
0

Mouse 568963 - Familiar - G - im036_r
Spikes: T=75, R=652, N=198

Mouse 572846 - Familiar - G - im036_r
Spike Rate Dist.

0.04

0.3

20 25
Spike Rate

0.01

0

Active Behavior
Passive Replay

0.2

15

0.02

40

0.05

0.1

10

10

60

0.7

5

20

Mouse 572846 - Familiar - G - im036_r
Spikes: T=75, R=496, N=155
0.06

0.03

0.07

20
0.1

0.04

0.08

Spike Probability

Neuron Count

0.04

0

Mouse 527749 - Familiar - G - im036_r
Spike Rate Dist.

0.05

0.06

Active Behavior
(CV=1.55)
Passive Replay
(CV=1.24)

80

0.05

0

0.7

Active Behavior
Passive Replay

0.07

Spike Probability

Spike Probability
Spike Probability

15

100

0.06

0.6

0.06

Mouse 570301 - Familiar - G - im036_r
Spike Rate Dist.

0.01

Spike Probability

35

50

0

0.02

Spike Probability

10

70

0.7

0.5

0.01

80

Neuron Count
0.1

0.07

R: Mean=566.08, Std=57.66, Min=356, Max=652
Min Mouse ID=578257, Max Mouse ID=568963
N: Mean=154.81, Std=48.44, Min=42, Max=240
Min Mouse ID=541234, Max Mouse ID=570299

60
40
20

0.01
0.00
0.0

30

60

0.08

0.06

20 25
Spike Rate

20

Mouse 570301 - Familiar - G - im036_r
Spikes: T=75, R=536, N=220

0.00
0.0

15

Mouse 560770 - Familiar - G - im036_r
Spike Rate Dist.

Active Behavior
Passive Replay

0.4
Time [s]

0.07

Active Behavior
(CV=1.11)
Passive Replay
(CV=1.52)

Mouse 560770 - Familiar - G - im036_r
Spikes: T=75, R=568, N=169

0.00
0.0

10

30

0

0.7

0.3

0.08

Spike Probability

Spike Probability

Neuron Count
0.3

0.2

0.01

Mouse 527749 - Familiar - G - im036_r
Spikes: T=75, R=619, N=135

10
0.2

0.1

0.01

50

0.02
0.1

0.00
0.0

0.02

40

0.04

0.08
0.07
0.06
0.05
0.04
0.03
0.02
0.01
0.00
0.0

45

Mouse 563323 - Familiar - G - im036_r
Spike Rate Dist.

0.06

0.00
0.0

40

Active Behavior
(CV=1.65)
Passive Replay
(CV=1.15)

Mouse 563323 - Familiar - G - im036_r
Spikes: T=75, R=635, N=116
0.08

35

0.02

Neuron Count

0.06

0.1

30

Spike Probability

Neuron Count

Spike Probability

0.08

0.00
0.0

20 25
Spike Rate

Mouse 533539 - Familiar - G - im036_r
Spike Rate Dist.

Active Behavior
Passive Replay

0.10

15

0.03

Neuron Count

Mouse 533539 - Familiar - G - im036_r
Spikes: T=75, R=634, N=149

10

0.04

Neuron Count

5

0.05

80

Neuron Count

0

Mouse 558306 - Familiar - G - im036_r
Spike Rate Dist.

Active Behavior
Passive Replay

Neuron Count

0

0.7

Neuron Count

0.6

Neuron Count

0.5

20

Neuron Count

0.4
Time [s]

40

Neuron Count

0.3

60

Neuron Count

0.2

0.04
0.02

10
0.1

0.06

Spike Probability

20

Spike Probability

30

Spike Probability

0.02

40

Mouse 558306 - Familiar - G - im036_r
Spikes: T=75, R=573, N=179

0.06

Spike Probability

0.04

80

0.08

0.07

Active Behavior
(CV=1.93)
Passive Replay
(CV=1.56)

100

Spike Probability

0.06

Active Behavior
Passive Replay

0.10
Spike Probability

50

0.08

0.00
0.0

Active Behavior
(CV=1.51)
Passive Replay
(CV=1.08)

60
Neuron Count

Spike Probability

0.10

(19 mice and after + Summary)

Mouse 563497 - Familiar - G - im036_r
Mouse 563497 - Familiar - G - im036_r
Spikes: T=75, R=539, N=195Familiar G im036_r
Spike Rate Dist.

Mouse 574082 - Familiar - G - im036_r
Spike Rate Dist.

Active Behavior
Passive Replay

Neuron Count

Mouse 574082 - Familiar - G - im036_r
Spikes: T=75, R=545, N=109

0.1

0.2

0.3

0.4
Time [s]

0.5

0.6

0.7

0

0

5

10

15

20 25
Spike Rate

30

35

40

45

Supplementary Fig. S3. Spike-rate dynamics and distributions for mice 19-37. The same as in Supplementary
Fig. S2 but for the remaining 19 mice.

Supplementary Fig. S4. Comparison of mean spiking probability and coefficient of variation in the active and
passive conditions. A Mean spiking probability across all bins, trials, and neurons in active and passive conditions. Each line
represents the same mouse. Neurons showed significantly lower firing rates in the active condition (p = 1.556 × 10−8 , Wilcoxon
signed-rank test). B Coefficient of variations (CVs) of the firing rate distributions, a measure of sparseness, in the active and
passive conditions. CV was significantly higher in the active condition (p = 8.35 × 10−8 , Wilcoxon signed-rank test).

Supplementary Fig. S5.
Mean effective coupling and shuffle control. A Violin plots of time-averaged effective
couplings for mouse 574078 under the active and passive conditions. Horizontal bars indicate the mean (red) and median
(green); points show individual entries. B Population summary of the per-mouse mean coupling in the original data; each
line connects the active and passive values from the same mouse. Panel annotations report p-values and sample size (n) from
Wilcoxon signed-rank tests across mice (two-sided). C Shuffle-adjusted means, where for each mouse the value in each condition
is computed as (Original − Shuffle); lines connect paired values. The annotation reports a one-sided Wilcoxon signed-rank test
assessing whether the median of {(Original − Shuffle) in Active} minus {(Original − Shuffle) in Passive} is greater than zero.
Together, the results indicate that the mean effective coupling is larger in the active condition than in the passive condition,
and that this increase persists after shuffle correction.

Supplementary Fig. S6. Time courses of entropy flow and mean spike rates for each mouse under active and
passive conditions. Each subplot represents the dynamics of an individual mouse. Solid lines are entropy flows (red for
active, blue for passive) while dashed lines represent the average population spike rate (red for active, blue for passive).

Supplementary Fig. S7. Comparison of shuffle-subtracted parameter variabilities and coupling asymmetry
with entropy flow for all mice. Each row represents comparisons of parameter variabilities and coupling asymmetry
(calculated by subtracting the shuffled-data estimate of the variance from the original-data estimate) and their relationship
to the shuffle-subtracted entropy flow. A, B, C “∆active” (shuffle-subtracted changes in the field, coupling variabilities, and
coupling asymmetry) versus the shuffle-subtracted entropy flow in the active state. D, E, F “∆passive” versus the shufflesubtracted entropy flow in the passive state.

A

Mouse 574078

B

Mouse 574078

C

D

Supplementary Fig. S8. Relating the dependency of entropy flow change of individual units on firing rates with
behavioral performance. A Mean spike rate vs entropy flow per individual unit under the active and passive conditions
(mouse 574078). Dashed lines connect values for the two conditions, highlighting behavioral state-dependent changes. B
Geometric mean spike rate (abscissa) vs differences in entropy flow (active - passive, ordinate) for individual units. The
positive Spearman correlation coefficient (ρ = 0.22) suggests that units with higher spike rates increased entropy flow in the
active condition. C (Left) Scatter plot of behavioral performance (mean d-prime) vs. the Spearman rank correlation between
the geometric mean rate and entropy flow change of individual units. Each dot represents a single mouse. The dependency in
this scatter plot was assessed again by the Spearman rank correlation coefficient, yielding ρ = 0.3578. (Right) A permutation
test comparing the observed correlation value ρ with those obtained from the surrogate data. A statistically significant positive
relationship was observed (p = 0.0304, two-tailed). The surrogate data was constructed by permuting the values of mean
d-prime. D Results for trial-shuffled data.

