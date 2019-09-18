from OpenSSL import crypto, SSL
from os.path import exists, join
from socket import gethostname
from pathlib import Path
import random


CERT_FILE="mycert.pem"
CLIENT_CERT="myclient.pem"
SERVER_CERT="myserver.pem"
KEY_FILE="mykey.key"
CLIENT_KEY="myclient.key"
SERVER_KEY="myserver.key"
INT_KEY_FILE="intkey.key"

CERT_DIR = Path("cert_dir/")


def create_self_signed_cert(cert_dir):
    """
    Create certificate and key for CA, server, and client.
    """

    # create a key pair
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 4096)

    # create a self-signed cert
    cert = crypto.X509()
    cert.get_subject().C = "US"
    cert.get_subject().ST = "New York"
    cert.get_subject().L = "New York"
    cert.get_subject().O = "MongoDB"
    cert.get_subject().OU = "SoftwareEng"
    cert.get_subject().CN = gethostname()
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365*24*60*60)
    cert.set_serial_number(random.randint(50000000,100000000))
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.add_extensions([
      crypto.X509Extension(b"subjectKeyIdentifier", False, b"hash",
                                    subject=cert),
      crypto.X509Extension(b"basicConstraints", True, b"CA:TRUE"),
      crypto.X509Extension(b"keyUsage", True,
                                   b"keyCertSign, cRLSign"),
      crypto.X509Extension(b"nsComment", False, b"OpenSSL Generated Certificate for TESTING only.  NOT FOR PRODUCTION USE."),
      crypto.X509Extension(b"extendedKeyUsage", False, b"serverAuth, clientAuth"),
      #crypto.X509Extension(b"authorityKeyIdentifier", False, b"keyid:always",issuer=cert)
      ])
    cert.sign(k, 'sha256')

    # create a key pair
    intermediateKey = crypto.PKey()
    intermediateKey.generate_key(crypto.TYPE_RSA, 4096)

    # create a self-signed cert
    intermediate_cert = crypto.X509()
    intermediate_cert.get_subject().C = "US"
    intermediate_cert.get_subject().ST = "New York"
    intermediate_cert.get_subject().L = "New York"
    intermediate_cert.get_subject().O = "MongoDB"
    intermediate_cert.get_subject().OU = "SoftwareEng"
    intermediate_cert.get_subject().CN = gethostname()
    intermediate_cert.gmtime_adj_notBefore(0)
    intermediate_cert.gmtime_adj_notAfter(365*24*60*60)
    intermediate_cert.set_serial_number(random.randint(50000000,100000000))
    intermediate_cert.set_issuer(cert.get_subject())
    intermediate_cert.set_pubkey(intermediateKey)
    intermediate_cert.add_extensions([
      crypto.X509Extension(b"subjectKeyIdentifier", False, b"hash",
                                    subject=intermediate_cert),
      crypto.X509Extension(b"basicConstraints", False, b"CA:TRUE"),
      crypto.X509Extension(b"keyUsage", True,
                                   b"keyCertSign, cRLSign"),
      crypto.X509Extension(b"nsComment", False, b"OpenSSL Generated Certificate for TESTING only.  NOT FOR PRODUCTION USE."),
      crypto.X509Extension(b"extendedKeyUsage", False, b"serverAuth, clientAuth"),
      #crypto.X509Extension(b"authorityKeyIdentifier", False, b"keyid:always",issuer=intermediate_cert)
      ])
    intermediate_cert.sign(intermediateKey, 'sha256')


    with open(join(cert_dir, CERT_FILE), "wb") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, intermediate_cert))

    with open(join(cert_dir, KEY_FILE), "wb") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))

    with open(join(cert_dir, INT_KEY_FILE), "wb") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, intermediateKey))

    client_key = crypto.PKey()
    client_key.generate_key(crypto.TYPE_RSA, 4096)

    client_cert = crypto.X509()
    client_cert.set_serial_number(random.randint(50000000,100000000))

    client_subj = client_cert.get_subject()
    client_subj.commonName = "Client"

    client_cert.add_extensions([
        crypto.X509Extension(b"basicConstraints", False, b"CA:FALSE"),
        crypto.X509Extension(b"subjectKeyIdentifier", False, b"hash", subject=client_cert),
    ])

    client_cert.add_extensions([
        crypto.X509Extension(b"authorityKeyIdentifier", False, b"keyid:always", issuer=cert),
        crypto.X509Extension(b"extendedKeyUsage", False, b"clientAuth"),
        crypto.X509Extension(b"keyUsage", False, b"digitalSignature"),
    ])

    client_cert.set_issuer(cert.get_subject())
    client_cert.set_pubkey(client_key)
    client_cert.gmtime_adj_notBefore(0)
    client_cert.gmtime_adj_notAfter(10*365*24*60*60)
    client_cert.sign(k, 'sha256')

    open(join(cert_dir, CLIENT_CERT), "wb").write(
        crypto.dump_certificate(crypto.FILETYPE_PEM, client_cert))
    open(join(cert_dir, CLIENT_KEY), "wb").write(
        crypto.dump_privatekey(crypto.FILETYPE_PEM, client_key))

    server_key = crypto.PKey()
    server_key.generate_key(crypto.TYPE_RSA, 4096)

    server_cert = crypto.X509()
    server_cert.set_serial_number(random.randint(50000000,100000000))

    server_subj = server_cert.get_subject()
    server_subj.commonName = "Server"
    server_subj.C = "US"
    server_subj.ST = "New York"
    server_subj.L = "New York"
    server_subj.O = "MongoDB"
    server_subj.OU = "SoftwareEng"

    server_cert.add_extensions([
        crypto.X509Extension(b"basicConstraints", False, b"CA:FALSE"),
        crypto.X509Extension(b"subjectKeyIdentifier", False, b"hash", subject=server_cert),
    ])

    server_cert.add_extensions([
        crypto.X509Extension(b"authorityKeyIdentifier", False, b"keyid:always", issuer=cert),
        crypto.X509Extension(b"extendedKeyUsage", False, b"serverAuth"),
        crypto.X509Extension(b"keyUsage", False, b"digitalSignature"),
        crypto.X509Extension(b"subjectAltName", False, b"DNS:mariamac"),
    ])

    server_cert.set_issuer(cert.get_subject())
    server_cert.set_pubkey(server_key)
    server_cert.gmtime_adj_notBefore(0)
    server_cert.gmtime_adj_notAfter(10*365*24*60*60)
    server_cert.sign(k, 'sha256')

    with open(join(cert_dir, SERVER_CERT), "wb") as f:
       f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, server_cert))
       f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, server_key))

create_self_signed_cert(CERT_DIR)
