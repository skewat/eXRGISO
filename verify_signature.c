#include <stdio.h>
#include <stdlib.h>
#include <openssl/pem.h>
#include <openssl/rsa.h>
#include <openssl/sha.h>

// 4096-bit RSA key produces 512 bytes signature.
#define BUFFER_SIZE 512

// Computes digest of the iso file using SHA256 Algorithm.
void readFile(FILE *datafile, unsigned char digest[]) {
	unsigned int bytes = 0;
	
	SHA256_CTX ctx;
	SHA256_Init(&ctx);
	unsigned char buffer[BUFFER_SIZE];
	
	// Read data in the datafile and feed it to SHA256 Algorithm.
	while((bytes = fread(buffer, 1, BUFFER_SIZE, datafile))) {
		SHA256_Update(&ctx, buffer, bytes);
	}

	SHA256_Final(digest, &ctx);
}

// Reads Signature from Signature File, returns the number of bytes read (BUFFER_SIZE).
unsigned int readSignatureFile(FILE *sign, unsigned char buffer[]) {
	unsigned int bytes = 0;

	bytes = fread(buffer, 1, BUFFER_SIZE, sign);
	return bytes;
}

// Reads Public Key from Public Key File.
RSA *readPublicKey(FILE *pubkey) {
	return PEM_read_RSA_PUBKEY(pubkey, NULL, NULL, NULL);
}

// Decrypt Signature (in buffer) and
// verify if the decrypted signature and the digest output matches each other.
// Returns 1 if matches, else 0.
int verify(unsigned char digest[], unsigned char buffer[], unsigned int bytes, RSA *rsa_pubkey) {
	int result;
	result = RSA_verify(NID_sha256, digest, SHA256_DIGEST_LENGTH, buffer, bytes, rsa_pubkey);
	return result;
}


int main (int argc, char *argv[]) {
	if (argc != 4) {
		fprintf(stderr, "Arguments: %s iso_file signature_file public_key\n", argv[0]);
		return -1;
	}

	const char *filename = argv[1];
	const char *sigfile = argv[2];
	const char *pubkeyfile = argv[3];
	
	unsigned int bytes = 0;
	unsigned char digest[SHA256_DIGEST_LENGTH];
	unsigned char buffer[BUFFER_SIZE];
	
	// Compute digest for iso file.
	FILE *datafile = fopen(filename, "rb");
	readFile(datafile, digest);
	fclose(datafile);
	
	// Read signature from file.
	FILE *sign = fopen(sigfile, "r");
	bytes = readSignatureFile(sign, buffer);
	fclose(sign);

	// Read Public Key from file.
	FILE *pubkey = fopen(pubkeyfile, "r");
	RSA *rsa_pubkey = readPublicKey(pubkey);
	fclose(pubkey);
	
	// Verify that computer digest and the decrypted signature match.
	int result = verify(digest, buffer, bytes, rsa_pubkey);
	RSA_free(rsa_pubkey);

	if(result == 1) {
		printf("Signature is valid.\n");
		return 0;
	}
	else {
		printf("Signature is invalid.\n");
		return 1;
	}
}
