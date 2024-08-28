#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 28 05:57:34 2024

PJD 28 Aug 2024     - Started
PJD 28 Aug 2024     - Working version for CMIP3, 5 and 6
PJD 28 Aug 2024     - Updated to count tables as well
                    TODO: Determine variables written to CMIP3,
                     5 and 6 ESGF archives

@author: durack1
"""

# %% imports
import glob
import hashlib
import json
import os

# %% function defs


def readJsonTable(tableFilePath) -> dict:
    with open(tableFilePath, "r") as f:
        aDic = json.load(f)

    return aDic


def readTxtTable(tableFilePath) -> dict:
    """
    function lifted from the CMOR2.8 library, see
    https://github.com/PCMDI/cmor/blob/CMOR-2.8.0/Lib/check_CMOR_compliant.py#L119-L199
    """

    lists_kw = [
        "requested",
        "bounds_requested",
        "z_factors",
        "z_bounds_requested",
        "dimensions",
        "required",
        "ignored",
        "optional",
    ]
    f = open(tableFilePath, "r", encoding="utf-8")
    blob = f.read().encode("utf-8")
    m5 = hashlib.md5(blob)
    m5 = m5.hexdigest()
    f.seek(0)
    ln = f.readlines()
    f.close()
    header = 1
    gen_attributes = {"actual_md5": m5}
    while header:
        l = ln.pop(0)[:-1]
        l = l.strip()
        if l == "" or l[0] == "!":
            continue
        sp = l.split("_entry")
        if len(sp) > 1:
            ln.insert(0, l + "\n")
            header = 0
            continue
        sp = l.split(":")
        kw = sp[0]
        st = "".join(sp[1:])
        st = st.split("!")[0].strip()
        if st[0] == "'":
            st = st[1:-1]
        if kw in gen_attributes:
            if isinstance(gen_attributes[kw], str):
                gen_attributes[kw] = [gen_attributes[kw], st]
            else:
                gen_attributes[kw].append(st)
        else:
            gen_attributes[kw] = st
    e = {}  # entries dictionnary
    while len(ln) > 0:
        l = ln.pop(0)
        sp = l.split("_entry:")
        entry_type = sp[0]
        entry = sp[1].strip()
        if not entry_type in e:
            e[entry_type] = {}
        e[entry_type][entry] = e[entry_type].get(entry, {})

        # print(e[entry_type][entry])
        cont = 1
        while cont:
            l = ln.pop(0)[:-1]
            l = l.strip()
            if l == "" or l[0] == "!":
                if len(ln) == 0:
                    cont = 0
                continue
            sp = l.split("_entry:")
            if len(sp) > 1:
                ln.insert(0, l + "\n")
                cont = 0
            sp = l.split(":")
            kw = sp[0].strip()
            val = ":".join(sp[1:]).split("!")[0].strip()
            # print("dic is:", e[entry_type][entry])
            if kw in e[entry_type][entry]:
                if kw in lists_kw:
                    e[entry_type][entry][kw] = "".join(e[entry_type][entry][kw])
                e[entry_type][entry][kw] += " " + val
            else:
                e[entry_type][entry][kw] = val
                # print("After:", e[entry_type][entry][kw])
            if kw in lists_kw:
                # print("splitting:", kw, e[entry_type][entry][kw].split())
                e[entry_type][entry][kw] = e[entry_type][entry][kw].split()
            if len(ln) == 0:
                cont = 0
    e["general"] = gen_attributes

    return e


def trimReportVar(tableDict, key) -> list:
    """
    Take a table dictionary, parse the variable subDict and report
    """
    cmipCoords = [
        "a",
        "a_bnds",
        "ap",
        "ap_bnds",
        "az",
        "az_bnds",
        "b",
        "b_bnds",
        "bz",
        "bz_bnds",
        "p0",
        "ptop",
        "sigma",
        "sigma_bnds",
    ]
    varKeys = list(tableDict[key].keys())
    # trim out coord vars
    varList = [x for x in varKeys if x not in cmipCoords]
    lenVarList = len(varList)
    print("len(varList):", lenVarList)
    print("varList:", varList)

    return lenVarList


def reportMipEra(tablePath, mipId) -> None:
    print("Processing:", mipId)
    tableFiles = glob.glob(os.path.join(tablePath))
    # catch non-Table files
    nonTable = [
        "CMIP5_grids",  # CMIP5
        "CMIP6_coordinate.json",
        "CMIP6_formula_terms.json",
        "CMIP6_input_example.json",
        "CMIP6_CV.json",
        "md5s",  # CMIP5
    ]
    varCount, tableCount = [0 for _ in range(2)]
    for table in tableFiles:
        # check for non-Table files
        if table.split("/")[-1] in nonTable:
            print("skipping:", table)
            print("-----")
            continue
        print("table:", trimPath(table))
        tableCount = tableCount + 1
        if mipId == "CMIP6":
            aDic = readJsonTable(table)
            key = "variable_entry"
        else:
            aDic = readTxtTable(table)
            key = "variable"
        cnt = trimReportVar(aDic, key)
        varCount = varCount + cnt
        print("-----")
    print("total", mipId, "tables:", tableCount, "vars:", varCount)


def trimPath(filePath):
    """
    trim local path
    """
    filePath = filePath.replace("/Users/durack1/sync/git/", "")

    return filePath


# %% start to iterate over tables
reportMipEra("/Users/durack1/sync/git/cmip3-cmor-tables/Tables/*", "CMIP3")
print("-----")
print("-----")
reportMipEra("/Users/durack1/sync/git/cmip5-cmor-tables/Tables/*", "CMIP5")
print("-----")
print("-----")
reportMipEra("/Users/durack1/sync/git/cmip6-cmor-tables/Tables/*", "CMIP6")
