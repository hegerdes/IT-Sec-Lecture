# Proxy Evaluation

## Iperf setup

### Config
```bash
# server
iperf -s -i 0.5 -N -p 2622

#client
iperf -c bones.informatik.uni-osnabrueck.de -i 0.5 -p 2622 -N -n 16MB

# -i for updat intervall
# -N to disale Nagle's Algorithm (Package buffering)
# -n size of files to transmit
# -p Port
```

```bash
#capture
sudo tcpdump -s 96 -n -e -i eth0 -w evaluation.pcap port 2622 or port 6622 or port 7622 or port 8622 or port 9622 or port 2222
```

### Restrictions
No bidirectiona because it needs reverse route and that does not work if client is behind NAT. iperf3 fixes that.