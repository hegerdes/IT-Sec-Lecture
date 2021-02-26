#!/usr/bin/python3
import os
import argparse
import numpy as np
import matplotlib.pyplot as plt


header=['NoProxy', 'ProxyNoSSL', 'ProxyServerSSL', 'ProxyServerClientSSL', 'ProxyServerClientSSLACL', 'SSHTunnel']

def parseLogs(file_path):
    test_type = ''
    res = []
    results = {}

    with open(file_path, 'r') as fr:
        line = fr.readline().strip()
        while line:
            if line in header:
                tmp = []
                test_type = line
                for i in range(7): line = fr.readline().strip()

                while line not in header:
                    if not line: break
                    # print(test_type, line)
                    tmp.append(evalLogLine(line))
                    line = fr.readline().strip()
                res.append(tmp)
            else:
                line = fr.readline().strip()

    for i in range(len(res)):
        print('Throughput [0.5s]:', res[i])
        if i%len(header) == 0:
            if 'NoProxy' not in results:
                results['NoProxy'] = []
            results['NoProxy'].append(list(res[i]))
        if i%len(header) == 1:
            if 'ProxyNoSSL' not in results:
                results['ProxyNoSSL'] = []
            results['ProxyNoSSL'].append(list(res[i]))
        if i%len(header) == 2:
            if 'ProxyServerSSL' not in results:
                results['ProxyServerSSL'] = []
            results['ProxyServerSSL'].append(list(res[i]))
        if i%len(header) == 3:
            if 'ProxyServerClientSSL' not in results:
                results['ProxyServerClientSSL'] = []
            results['ProxyServerClientSSL'].append(list(res[i]))
        if i%len(header) == 4:
            if 'ProxyServerClientSSLACL' not in results:
                results['ProxyServerClientSSLACL'] = []
            results['ProxyServerClientSSLACL'].append(list(res[i]))
        if i%len(header) == 5:
            if 'SSHTunnel' not in results:
                results['SSHTunnel'] = []
            results['SSHTunnel'].append(list(res[i]))

    return results

def evalLogLine(log_line):
    return float(log_line.split()[6])

def checkAVG(data):
    out = {}
    for key in data.keys():
        out[key] = []

    for key, val in data.items():
        for test in val:
            out[key].append(*test[-1:])
            print('CalcedAVG: {:.2f}\tOfficialAVG: {:3.2f}'.format(sum(test[:-1])/len(test[:-1]), test[-1]))

    return out

def plot(data):
    plt.rcParams['ytick.labelsize'] = "small"
    ax = plt.figure(figsize=(12.5, 8.5), dpi=150).add_subplot()
    ax.set_title('Proxy throughput results')
    ax.boxplot(list(data.values()), notch=True, vert=False, meanline=True)

    ax.set_yticklabels(data.keys())
    ax.set_xlabel('Mbits')
    plt.savefig('docs/fig/boxplot.pdf')
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Lunches an iperf logparser')
    parser.add_argument('--file', '-f', help='Path to logfile[s]', default='evaluation/iperf_diggory.log',required=True, nargs='+')

    args = parser.parse_args()
    res = dict(zip(header, [[] for i in range(len(header))]))
    [[res[k].extend(v) for k, v in checkAVG(parseLogs(log_path)).items()] for log_path in args.file]
    print(res)
    [print('Mean: {:.2f} Std: {:.2f} Var: {:.2f} for {}'.format(np.mean(np.array(v)), np.std(np.array(v)), np.var(np.array(v)), k)) for k, v in res.items()]
    print('Parsed {} interations.\nFor every configuration {}'.format(len(res['NoProxy']) * len(header), len(res['NoProxy'])))

    # plot(res)