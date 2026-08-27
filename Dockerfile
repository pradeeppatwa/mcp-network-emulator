# Custom image for MCP Network Emulator
# Extends ramonfontes/bmv2 with network measurement tools
FROM ramonfontes/bmv2

# Install iperf and telnet required for net.iperf() measurement
RUN apt-get update && \
    apt-get install -y iperf telnet iproute2 iputils-ping && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Default command
CMD ["/bin/bash"]
