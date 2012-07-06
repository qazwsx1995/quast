############################################################################
# Copyright (c) 2011-2012 Saint-Petersburg Academic University
# All Rights Reserved
# See file LICENSE for details.
############################################################################

import os
import re


#txt_pattern = re.compile(r'gi\|(?P<id>\d+)\|\w+\|(?P<seqname>\S+)\|\s+(?P<number>\d+)\s+(?P<start>\d+)\s+(?P<end>\d+)', re.I)   # not necessary starts with "gi"
txt_pattern = re.compile(r'(?P<seqname>\S+)\s+(?P<id>\d+)\s+(?P<start>\d+)\s+(?P<end>\d+)', re.I)
ncbi_start_pattern = re.compile(r'(?P<number>\d+)\.\s*(?P<name>\S+)\s*$', re.I)
gff_pattern = re.compile(r'(?P<seqname>\S+)\s+\S+\s+(?P<feature>\S+)\s+(?P<start>\d+)\s+(?P<end>\d+)\s+\S+\s+(?P<strand>[\+\-]?)\s+\S+\s+(?P<attributes>\S+)', re.I)

def get_genes_from_file(filename, feature):
    if not filename or not os.path.exists(filename):
        print '  Warning! ' + feature + '\'s file not specified or doesn\'t exist!'
        return []

    genes_file = open(filename, 'r')
    genes = None

    line = genes_file.readline().rstrip()
    while line == '' or line.startswith('##'):
        line = genes_file.readline().rstrip()

    genes_file.seek(0)

    if txt_pattern.match(line):
        genes = parse_txt(genes_file)

    elif gff_pattern.match(line):
        genes = parse_gff(genes_file, feature)

    elif ncbi_start_pattern.match(line):
        try:
            genes = parse_ncbi(genes_file)
        except ParseException as e:
            print '  ', e
            print '    ' + filename + ' skipped'
            genes = []

    else:
        print '  Warning! Incorrect format of ' + feature + '\'s file! Specify file in plaint TXT, GFF or NCBI format!'
        print '    ' + filename + ' skipped'

    genes_file.close()
    return genes


# parsing NCBI format

# EXAMPLE:
#   1. Phep_1459
#   heparinase II/III family protein[Pedobacter heparinus DSM 2366]
#   Other Aliases: Phep_1459
#   Genomic context: Chromosome
#   Annotation: NC_013061.1 (1733715..1735595, complement)
#   ID: 8252560
def parse_ncbi(file):
    annotation_pattern = re.compile(r'Annotation: (?P<seqname>\S+) \((?P<start>\d+)\.\.(?P<end>\d+)(, complement)?\)', re.I)
    id_pattern = re.compile(r'ID: (?P<id>\d+)', re.I)

    genes = []

    line = file.readline()
    while line != '':
        while line.rstrip() == '' or line.startswith('##'):
            if line == '':
                break
            line = file.readline()

        m = ncbi_start_pattern.match(line.rstrip())
        if m:
            gene = Gene(number=int(m.group('number')), name=m.group('name'))

            another_gene_info_lines = []

            line = file.readline()
            while line != '' and not ncbi_start_pattern.match(line.rstrip()):
                another_gene_info_lines.append(line.rstrip())
                line = file.readline()


            for info_line in another_gene_info_lines:
                if info_line.startswith('Annotation:'):
                    m = re.match(annotation_pattern, info_line)
                    if m:
                        gene.seqname = m.group('seqname')
                        gene.start = int(m.group('start'))
                        gene.end = int(m.group('end'))
                    else:
                        raise ParseException('NCBI format parsing error: wrong annotation for gene ' + gene.number + '. ' + gene.name + '.')

                if info_line.startswith('ID:'):
                    m = re.match(id_pattern, info_line)
                    if m:
                        gene.id = m.group('id')
                    else:
                        raise ParseException('NCBI format parsing error: wrong ID for gene ' + gene.number + '. ' + gene.name + '.')


            if not (gene.start is not None and gene.end is not None):
                raise ParseException('NCBI format parsing error: provide start and end for gene ' + gene.number + '. ' + gene.name + '.')

            genes.append(gene)

        else:
            raise ParseException("NCBI format parsing error")

    return genes


# parsing txt format

# EXAMPLE:
#   gi|48994873|gb|U00096.2|	1	4263805	4264884
#   gi|48994873|gb|U00096.2|	2	795085	795774
def parse_txt(file):
    genes = []

    for line in file:
        m = txt_pattern.match(line)
        if m:
            gene = Gene(id=m.group('id'), seqname=m.group('seqname'))
            s = int(m.group('start'))
            e = int(m.group('end'))
            gene.start = min(s, e)
            gene.end = max(s, e)
            genes.append(gene)

    return genes


# parsing GFF

# EXAMPLE:
#   ##gff-version   3
#   ##seqname-region   ctg123 1 1497228
#   ctg123 . gene            1000  9000  .  +  .  ID=gene00001;Name=EDEN
#   ctg123 . TF_binding_site 1000  1012  .  +  .  ID=tfbs00001;Parent=gene00001
def parse_gff(file, feature):
    genes = []

    number = 0

    for line in file:
        m = gff_pattern.match(line)
        if m and m.group('feature') == feature:
            gene = Gene(seqname = m.group('seqname'), start = int(m.group('start')), end = int(m.group('end')))

            attributes = m.group('attributes').split(';')
            for attr in attributes:
                key, val = attr.split('=')
                if key == 'ID':
                    gene.id = val

            if gene.id is None:
                gene.id = number
            number += 1

            genes.append(gene)

    return genes



class ParseException(Exception):
    def __init__(self, value, *args, **kwargs):
        super(ParseException, self).__init__(*args, **kwargs)
        self.value = value
    def __str__(self):
        return repr(self.value)

class Gene():
    def __init__(self, id=None, seqname=None, start=None, end=None, number=None, name=None):
        self.id = id
        self.seqname = seqname
        self.start = start
        self.end = end
        self.number = number
        self.name = name
