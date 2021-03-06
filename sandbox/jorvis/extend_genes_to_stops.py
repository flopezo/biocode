#!/usr/bin/env python3

'''
This script reads a GFF3 file and FASTA file (or FASTA embedded in the GFF) and
checks the translation of all CDS for internal stops.  

    Total mRNAs found:4091
    mRNAs with embedded stops: 895



Follow the GFF3 specification!

Author:  Joshua Orvis
'''

import argparse
import os
import biocodegff
import biocodeutils


def main():
    parser = argparse.ArgumentParser( description='Checks the CDS features against a genome sequence to report/correct phase columns.')

    ## output file to be written
    parser.add_argument('-i', '--input_file', type=str, required=True, help='Path to the input GFF3' )
    parser.add_argument('-g', '--genome_fasta', type=str, required=False, help='Optional.  You must specify this unless the FASTA sequences for the molecules are embedded in the GFF')
    parser.add_argument('-o', '--output_gff', type=str, required=False, help='Optional.  Writes an output GFF3 file with CDS (and containing features) extended to nearest stop')
    args = parser.parse_args()

    (assemblies, features) = biocodegff.get_gff3_features( args.input_file )

    # deal with the FASTA file if the user passed one
    if args.genome_fasta is not None:
        biocodeutils.add_assembly_fasta(assemblies, args.genome_fasta)

    total_mRNAs = 0
    mRNAs_with_terminal_stops = 0
    stop_codons = ['TAG', 'TAA', 'TGA']

    for assembly_id in assemblies:
        print("Assembly {0} has length {1}".format(assembly_id, assemblies[assembly_id].length))
        for gene in assemblies[assembly_id].genes():
            for mRNA in gene.mRNAs():
                coding_seq = mRNA.get_CDS_residues()
                total_mRNAs += 1
                translation = biocodeutils.translate(coding_seq)

                if translation.endswith('*'):
                    mRNAs_with_terminal_stops += 1
                else:
                    print("gene:{1}, mRNA: {0} is missing a stop".format(mRNA.id, gene.id))
                    mRNA_loc = mRNA.location_on(assemblies[assembly_id])
                    
                    CDSs = sorted(mRNA.CDSs())
                    codon_step_size = 3

                    if mRNA_loc.strand == 1:
                        CDS_pos = CDSs[-1].location_on(assemblies[assembly_id]).fmax
                        mRNA_limit = mRNA_loc.fmax
                    else:
                        CDS_pos = CDSs[0].location_on(assemblies[assembly_id]).fmin
                        mRNA_limit = mRNA_loc.fmin
                        codon_step_size = -3

                    print("\tmRNA:{0}-{1}, CDS end: {2}\n\tExtending".format(mRNA_loc.fmin, mRNA_loc.fmax, CDS_pos), end='')

                    new_stop_found = False

                    # We have to step backwards to start if on the reverse strand
                    if codon_step_size < 0:
                        CDS_pos += codon_step_size

                    while True:
                        if (codon_step_size < 0 and CDS_pos < mRNA_limit) or (codon_step_size > 0 and CDS_pos > mRNA_limit):
                            print(" Reached the mRNA limit")
                            break
                        else:
                            next_codon = assemblies[assembly_id].residues[CDS_pos:CDS_pos + 3]
                            print(".{0}({1})".format(next_codon, CDS_pos), end='')
                        
                            if next_codon in stop_codons:
                                new_stop_found = True
                                print(" Found a stop")
                                break

                        CDS_pos += codon_step_size

                    if new_stop_found == True:
                        print("\tCDS_pos: UPDATE: {0}".format(CDS_pos))
                    else:
                        print("\tCDS_pos:   SAME: {0}".format(CDS_pos))


    print("\nTotal mRNAs found:{0}".format(total_mRNAs))
    print("mRNAs with terminal stops: {0}".format(mRNAs_with_terminal_stops))


if __name__ == '__main__':
    main()






