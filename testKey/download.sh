echo "start download script."
mkfs.ext4 /dev/sdb
mkfs.ext4 /dev/sdc
mkfs.ext4 /dev/sdd
mkfs.ext4 /dev/sde
mkfs.ext4 /dev/sdf
mkdir /data/
mkdir /data/data0
mkdir /data/data1
mkdir /data/data2
mkdir /data/data3
mkdir /data/data4
mount /dev/sdb /data/data0
mount /dev/sdc /data/data1
mount /dev/sdd /data/data2
mount /dev/sde /data/data3
mount /dev/sdf /data/data4

wget https://github.com/ethersphere/bee/releases/download/v0.6.2/bee_0.6.2_amd64.deb -o ~/bee_0.6.2_amd64.deb
wget https://github.com/ethersphere/bee-clef/releases/download/v0.4.12/bee-clef_0.4.12_amd64.deb -o ~/bee-clef_0.4.12_amd64.deb
dpkg -i ~/bee_0.6.2_amd64.deb
dpkp -i ~/bee-clef_0.4.12_amd64.deb
systemclt stop bee
cp -r config/* /etc/bee-clef/
cp -r files/* /var/lib/bee-clef/
systemclt restart bee-clef
echo "finish"