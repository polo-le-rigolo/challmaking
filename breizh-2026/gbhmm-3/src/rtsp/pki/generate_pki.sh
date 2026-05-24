#!/bin/bash

set -e

read -p "Server domain name: " DOMAIN
read -p "Device Common Name (example: fr-relay-03): " DEVICE_CN
read -p "Output directory [pki]: " OUTDIR

OUTDIR=${OUTDIR:-pki}

mkdir -p "$OUTDIR"
cd "$OUTDIR"

echo
echo "[*] Generating CA private key..."
openssl genrsa -out ca.key 4096 >/dev/null 2>&1

echo "[*] Generating CA certificate..."
openssl req -x509 -new -nodes \
    -key ca.key \
    -sha256 \
    -days 3650 \
    -out ca.crt \
    -subj "/CN=Firmware Update Root CA" \
    >/dev/null 2>&1

echo "[+] CA generated"
echo

echo "[*] Generating server private key..."
openssl genrsa -out server.key 2048 >/dev/null 2>&1

echo "[*] Creating server OpenSSL config..."

cat > server.cnf <<EOF
[req]
distinguished_name=req_distinguished_name
prompt=no
req_extensions=v3_req

[req_distinguished_name]
CN=${DOMAIN}

[v3_req]
subjectAltName=@alt_names

[alt_names]
DNS.1=${DOMAIN}
EOF

echo "[*] Generating server CSR..."
openssl req -new \
    -key server.key \
    -out server.csr \
    -config server.cnf \
    >/dev/null 2>&1

echo "[*] Signing server certificate with CA..."
openssl x509 -req \
    -in server.csr \
    -CA ca.crt \
    -CAkey ca.key \
    -CAcreateserial \
    -out server.crt \
    -days 825 \
    -sha256 \
    -extfile server.cnf \
    -extensions v3_req \
    >/dev/null 2>&1

echo "[+] Server certificate generated"
echo

echo "[*] Generating device private key..."
openssl genrsa -out device.key.pem 2048 >/dev/null 2>&1

echo "[*] Generating device CSR..."
openssl req -new \
    -key device.key.pem \
    -out device.csr \
    -subj "/CN=${DEVICE_CN}" \
    >/dev/null 2>&1

echo "[*] Signing device certificate with CA..."
openssl x509 -req \
    -in device.csr \
    -CA ca.crt \
    -CAkey ca.key \
    -CAcreateserial \
    -out device.pem \
    -days 365 \
    -sha256 \
    >/dev/null 2>&1

echo "[+] Device certificate generated"
echo

echo "[*] Generating browser-importable PKCS12 bundle..."
openssl pkcs12 -export \
    -inkey device.key.pem \
    -in device.pem \
    -certfile ca.crt \
    -out device.p12

echo "Generated files:"
echo

ls -1

echo
echo "-----------------------------------------"
echo "SERVER FILES:"
echo "  server.crt"
echo "  server.key"
echo
echo "CLIENT/DEVICE FILES:"
echo "  device.pem"
echo "  device.key.pem"
echo "  device.p12"
echo
echo "CA FILES:"
echo "  ca.crt"
echo "  ca.key"
echo "-----------------------------------------"
echo
echo "device.p12 can be imported into Firefox/Chrome."
echo
echo "IMPORTANT:"
echo "- Put server.crt/server.key on the server"
echo "- Put ca.crt in nginx ssl_client_certificate"
echo "- Put device.pem + device.key.pem in firmware"
echo
