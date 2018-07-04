# -*- coding: utf-8 -*-
"""
Plot VOTable
Created on Fri Apr 01 19:12:07 2016

@author: stijnc
"""

from astropy.io.votable import parse
import matplotlib.pyplot as plt

def find_subgroup(parent,group_name):
    """Find a subgroup in a group"""
    for group in parent.iter_groups():
        if group.name == group_name:
            return group

votable = parse("spenvis_export.vot")
resource = votable.resources[0]
table = resource.tables[0]
datagroup = table.groups[0]
iterationsgroup = find_subgroup(datagroup,"iterations")
iteration1group = find_subgroup(iterationsgroup,"0001")
useroutput = find_subgroup(iteration1group,".user-output")
sd2q_doses = find_subgroup(useroutput,"sd2q_doses")
dose = find_subgroup(sd2q_doses,"dose")
for param in dose.iter_fields_and_params():
    if param.name == "thickness":
        x = param.value
    if param.name == "totalDose":
        totalDose = param.value
    if param.name == "bremsstrahlungDose":
        bremsstrahlungDose = param.value
    if param.name == "electronDose":
        electronDose = param.value
#plotting
totalDoseLabel, = plt.plot(x, totalDose, 'r--', label="total")
bremsstrahlungDoseLabel, = plt.plot(x, bremsstrahlungDose, 'bs', label="bremsstrahlung")
electronDoseLabel, = plt.plot(x, electronDose, 'g^', label="electrons")
plt.title("4pi Dose at Centre of Spheres (Aluminium)")
plt.xlabel("Eqv Al Absorber Thickness ($mm$)")
plt.xlim([0,20])
#plt.xticks(range(20))
plt.ylabel("Dose in Si ($rad$)")
plt.ylim([1e-4,1e5])
plt.yscale('log')
plt.legend(handles=[totalDoseLabel, bremsstrahlungDoseLabel, electronDoseLabel])
plt.grid(True)
plt.show()