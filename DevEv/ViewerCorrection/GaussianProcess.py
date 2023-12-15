import numpy as np
import matplotlib.pyplot as plt
from argparse import ArgumentParser

from scipy.signal import find_peaks
from scipy.stats import multivariate_normal

def read_data(filename):
    import os
    if not os.path.exists(filename):
        print("file not found")
        exit()
    with open(filename, "r") as f:
        data = f.readlines()

    x_list, y_list = [], []
    count = 0
    for d in data:
        d = d.split(",")

        if len(d) == 10: 
            fid, x, y, z, y, p, r, _,_,_ = d
        elif len(d)== 18:
            fid, flag, flag_h, x, y, z, y, p, r, att0, att1, att2, xhl, yhl, zhl, xhr, yhr, zhr = d
        else: continue
        x_list.append([float(x), float(y), float(z), float(y), float(p), float(r)])
        count += 1
        y_list.append(int(fid))
        #if count > 2100: break
    x_list = np.array(x_list)
    x_list =  x_list[1:] - x_list[:-1]
    #y_list = np.linspace(0, 1, len(x_list))
    y_list = np.array(y_list[1:])
    return x_list, y_list


def GP(x_tr, tau = 20):
    mean, var, value = [], [], []
    N, D = x_tr.shape
    for t, x in enumerate(x_tr):
        tau_min = max(0,t-tau)
        tau_max = min(N,t+tau+1)

        segment = x_tr[tau_min:tau_max]
        mu = np.mean(segment, axis = 0)
        if np.nan in mu or np.inf in mu:
            print(t, tau_min, tau_max, segment.shape)
            exit()
        #temp = segment - mu
        #sigma = np.dot(temp.T, temp)/(tau+1)
        sigma = np.cov(segment.T)

        mvg = multivariate_normal(mean=mu, cov=sigma, allow_singular=True)
        v = mvg.logpdf(x)/ mu.shape[0]


        var.append(sigma)
        mean.append(mu)
        value.append(v)

    mean = np.array(mean)
    var = np.array(var)
    value = np.array(value)

    return mean, var, value

def get_uncertainty(x_tr, max_n=None):
    if type(x_tr) == list:
        x_tr = np.array(x_tr)
    mean, var, value = GP(x_tr)
    value = var.mean(-1).mean(-1)
    value = (value - min(value)) / (max(value) - min(value))
    #peaks, _ = find_peaks(value, height=max(0.05, value.mean() + 0.5*value.std() ), distance=30, prominence=0.01)
    peaks, _ = find_peaks(value, distance=30)
    selected = value[peaks]
    if max_n is not None:
        if len(peaks) < max_n: 
            mean, var, value = GP(x_tr, tau = 10)
            value = var.mean(-1).mean(-1)
            value = (value - min(value)) / (max(value) - min(value))
            peaks, _ = find_peaks(value, distance=30)
        ind_selected = value[peaks].argsort()[::-1]
        ind_selected = ind_selected[:max_n]
        selected = selected[ind_selected]
        peaks = peaks[ind_selected]
    return peaks, selected

def uncertainty(filename):

    x_tr, y_tr = read_data(filename)
    print(x_tr.shape)
    mean, var, value = GP(x_tr)
    
    value = var.mean(-1).mean(-1)
    value = (value - min(value)) / (max(value) - min(value))
    peaks, _ = find_peaks(value, distance=30)
    m = mean[:,0]

    err = np.sqrt(var[:, 0, 0])
    plt.plot(y_tr,  m+err, "--r", label='std', linewidth=1)
    plt.plot(y_tr,  m-err, "--r", linewidth=1)
    plt.plot(y_tr,  m, "-b", label='Mean')
    plt.title("GP")
    plt.ylabel("x Offset")
    plt.xlabel("Time")
    plt.legend()
    plt.savefig("GP_x.png")
    plt.close()

    plt.plot(y_tr,  value, "-g", label='logpdf')
    plt.plot(y_tr[peaks], value[peaks], "xk", label="selection")
    plt.title("Frame selection")
    plt.ylabel("logpdf")
    plt.xlabel("Time")
    plt.legend()
    plt.savefig("GP_selected.png")
    plt.close()


    peaks = [str(y_tr[p]) for p in peaks]
    #with open("data/results.txt","a") as f:
    #    f.write(",".join(peaks))
    return peaks

if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument("--num-samples", default=15, type=int)
    parser.add_argument("--show-plots", action="store_true")
    parser.add_argument("-f", default="C:/Users/nicol/Downloads/attC_DevEv_S20_06_Sync (1).txt", type=str)
    args = parser.parse_args()

    p = uncertainty(args.f)
    print(len(p))
    print(p)
    
