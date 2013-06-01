#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""from cms.models import *
>>> deme = Group.objects.get(pk=27)
>>> deme
<Group: Group[27] "Deme Dev Discussion">
>>> a = Person(name="blah")
>>> a.save()
>>> a
<Person: [58] "blah">
>>> m = Membership(collection=deme, item=a)
>>> m.save()
>>> m
<Membership: [59] "">
>>> for i in range(0,100):
...  a = Person(name="sdf%d"%(i))
...  a.save()
...  m = Membership(collection=deme, item=a)
...  m.save()"""


from django.core.management import setup_environ
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from deme_django import settings
setup_environ(settings)

from cms.models import *
from cms.permissions import all_possible_global_abilities
from modules.webauth.models import *
from modules.demeaccount.models import *
from django import db
import subprocess
import re
import time

names = ['Sandra Prescott','Kimberly OBrien','Sophia Newell','Lillian Edwards','Elizabeth OKeely','Anna Harrison','Alexandra McMurty','Charlotte Kipling','Phoebe Rogers','Carly Frazier','Megan Sandford','Josephine Bonnard','Natalie Danton','Cassidy Chaparro','Willa Hemingway','Eva Edwardo','Annabelle Faulkner','Hilary Javaris','Mandy Hankeem','Henrietta Arabell ','Lydia Durwood ','Rachael Sladkey','Angelica Dobrimire','Sylvia Lorenzo','Molly MacLaine','Veronica Conrad','Katarina Carmine','Hanna Mikhail','Nora Slavek','Margaret "Peggy" Mariposa','Madeline Parvel','Natasha Grigori','Kiera Askel','Briget Tito','Annika Lochlain','Tiffany Lancaster','Emily Ioannis','Alicia Campton','Isabel Travis','Lisa Varniman','Leah Sheldon','Victoria Biven','Barbara Lincolnheimer','Abigail Hendrikson','Taylor Knutt','Jennifer Matts','Elena Soledad','Lindsay Vladja','Kelly Boleslaw','Laura Williams','Patricia Charlston','Ingrid Anton','Tatiana Sergei','Karolina Wojtek','Judith Elepidea','Eliza Ferris','Donna Alessandro','Calista Sanders','Jasmyn Smith','Madison Guadelupe','Heidi Gundrun','Esmee Maxime','Cynthia Clive','Laila Kareem','Tisalina "Tisie" Addae','Magdalane Salahe','Emmaline Questyn','Hazel Kyan','Loretta Hamif','Payton Halliwell','Cordelia Zethus','Samantha Kellan','Hannah MacIntyre','Lily Deagan','Xia Yu Li','Nina Damarcus','Polly Wingate','Arden Fields','Katharine "Katie" Myers','Stacy Smith','Carla Greer','Corinne Pfeiffer','Sydney Chatwin','Alison Hendrik','Violet Christman','Vanessa Hidalgo','Penelope White','Pearl Hakon','Natalya Brecht ','Ida Willhelm','Cathryn Gilmer','Carolyn French','Gail Ervin ','Ramona Galbraith','Leila Rahil','Linda Grandas','Dahlia Kismet','Cynthia Gaenor','Sophie Dildier','Stephanie Hardwood','Phyliss Basset','Regina Brown','Beth Anskel','Juliet Danaus','Olivia Palemon','Hannah Diotima','Gladys Etaney','Eloise Digette','Lorelei Green','Tessa Eldon','Wanda Brencis','Louisa-Mae Kaufman','Georgia Heller','Cecilia Uchechi','Kathleen Jenci','Nelly Altmann','Janice Farmer','Rita Smith','Hope Sudbury ','Imogen Muldoon','Catharine Otaki','Ruth Harrel','Mable Hendrikson','Jessica Cladwell','Hellen Markell','Florence Tyman','Eleanor Kacey','Maya Damon ','Zoe Ysolde','Lena Violanth','Chloe Zalika','Delilah Pickford','April Leland','Monica Jonley','Ivy Aymas','Aileen Dickinson','Nancy Trenica','Myrna Parryth','May Lathrop','Libby Kyros','Jenny McGowan','Dina Reynolds','Antionette Vyera','Allegra Hampton','Bertha Glennon','Peony Galmut','Rebecca Pacian','Amanda Finley','Claire Derwin','April Li','Brenda Codwell','Jill Valen','Gloria Brooke','Janet Moss','Eve Wilmot','Anne Ethelbert','Ethel Beaumont','Maria Semele','Paula Cathmoore','Stacy Connor','Loretta Hamoth','Paige Teo','Celia Janusa','Agnes Priti','Lucy Layings','Dorothy Pender','Fiona Odeen','Monica Heshire','Misha Cadbee','Emma Rodgers ','Sierra Kalgan','Alexis Garton','Hayley McFaybryce ','Piper Boswell','Kate Hanford','Lena Crompton','Sara Earvin','Ebba Adonijah','Flora Belden','Betty Charlston','Emily Robertson','Tracy Calek','Alexandria Wilming','Xia-Tu Zhong','Diane Fremont','Mary Altre','Pamela Amund','Ruby Netzer','Brittany Leonard','Sophie Orth','Miranda Kaven','Yvette Chanoch','Moira Emerson','Rhoda Hunt','Cathy Armithan','Raven McGregor','Lisa Takayren','Abigail Henson','Meghan Castulo','Kayley Macdowell','Heather Odhran','Michelle Ginton','Susan Ingleberte','Melissa Kyler','Mary Royden','Sarah Stillman','Amber Walter-Lawrence','Amanda Gasspardde','Alexis Brewsterr','Grace Cudjo','Melissa Gaius','Bess Kytzer','Delilah Landis','Alyssa Maxwell-Bodes ','Haleigh Severn','Delores Whites','Malia Sandhurst','Katarina Balraj','Savannah Jenkins','Mandy Tyrell','Mary Joaquin','Linda Sullivan','Patricia Codgell','Susan Akwete','Deborah Tapice','Barbara Lane','Karen Baldridge','Nancy Broughton','Donna Thandiwey','Cynthia Brooks','Pamela Izaak','Paloma Kerr','Sydda Zaltana','Emmie TeQuarius','Kathleen Boden','Kimberly Ozelle','Michelle Dabney','Tammy Eldon-Lee','Laura Thorburnt','Jeniffer Jindrich','Melissa Geary','Amy Lawton','Lisa Murray','Angela McLean','Heather Gockley','Stephanie Hilderbrand','Jessica Ilom','Elizabeth Ludolph','Nicole Freemont','Rebekkah Loman','Amanda Tippette','Ashley Dalton','Tiffany Zoltan','Rachael Landyre','Samantha Frode','Brittany Heschell','Kayla Nash','Madison Belle','Abigail Kayven','Isabella Prestlay','Alexis Koshey','Sophia Westolle','Betty Gerhard','Carla Arturian','Delores Gino','Frances Witold','Judy Folker','Nina Clements','Nadia Dawud','Priscilla Ainslley','Stacey Farris','Veronica Anzlem','Wanda Zbigniew','Elise Hyatt','Gail Burrick','Brooke Padden','Anna Kaughmann','Stacey Thompson','Elaine Kaemon','Ella Garthay-Davis','Linnea Gilette','Rita Brown','Phyllis Millam','Hildergard "Hildy" White','Suzanne Orris','Stephanie Sostrange','Sydonie West','Eliza Wood','Tara Smith','Sofia Ginsley','Marcie Okath','Desiree Jones','Elaine OCaley','Caroline Rhys','Abigail Kraig','Bertha Haafiz','Carolyne Brette','Doris Noor','Ellie Matlandde','Fuschia Yurik','Gretta Mitchum','Heloise Grace','Inez Juanantonio','Jessica Hall','Kaitlyn Reith','Lymeka Kedem','Madeleine Galloway','Noa Shnyer','Opal Tsaline','Penelope Stillmann','Qitarah McCovven','Rachael Osborne','Sarah Langford','Tatanya Birkley','Una Covet','Vivica Eaton','Wendy Yeslin','Xena Williams','Yvette Jean-Coll','Zoë Martin','Bridget Nelson','Camille Haines','Denice Wllies','Emma MacDowell','Flora Barnett-Giles','Grace Yon','Hildergard Balendin','Ilay Haute','Jenna Eldwood','Kasey Therman','Lia Belmount','Mina Irodell','Nancy Deinorus','Ophelia Jaggar','Prudence Rymann','Queenie Thorne','Rita Wilder','Stefany Pickford','Tiffany Witter','Ursla Njørd','Vera Esmond','Willa Smedly','Xanthe Lenard','Yolanda Tyson','Zora Leric','Anika Lavan','Lisa Kerrick','Stephanie Maddar','Harper Stronum','Lily Tack','Delondra Oneil','Fira Nilson','Tina Sawyer','Eritaña Lavi','LuLu McElhanny','Enya dAndous','Chloe Edqist','Zoe Krause','Ella VanDelori','Gabrielle deAugmann','Kathleen Albertine','Veronica Austin-Gabri','Kendall-Lee Rice','Sophia Mack','Louisa Gertstein','Freyja Gibbons','Kelsey Loch-Heimen','Emmilynn Triss','Lola Lansky','Sara Selipsky','Katie Noon','Paizley Wille','Piper Lapsley','Abby Fith','Sonja Rapture','Cicily Green','Anna Allard','Xemx "Sun" Qamar "Moon"','Dora Tann','Sylvie Sonolie','Bella Farhann','Emily Wentte','Anneka Farscal','Sarah Liite','Aude VanTrausselstaufe','Kyla Crouch','Zoe Steinberg','Dani Larutan','Lauren Roval','Silver Eulgra','Eugenia Conn','Adele Dessin','Agnes Etienne','Annie Brown','Bernadette Gauthier','Cecile VanTrop','Julie Pffiefer','Estelle Olsen','Diane Koffy','Lisette DeWitt','Giselle Andal','Louise Thierry','Monique Calde','Pauline Otomo','Sara Kazersky','Suzanne Reynelle','Sylvie Fisher','Genevieve Mathieu','Marie Goldstein','Maria Staren','Jaquelyn Franks','Mirielle Rousseau','Veronica Gerard-VanAusselstaute','Nicole Avery']
discuss_group = Group.objects.get(name="Deme Dev Discussion")
admin = Agent.objects.get(pk=1)
from django.template.defaultfilters import slugify

for name in names:
    print name
    split = name.split(' ')
    mike = Person(first_name=split[0], last_name=split[1], name=name)
    mike.save_versioned(action_agent=admin)
    permission = OneToOnePermission(source=mike, target=mike, ability='do_anything', is_allowed=True)
    mike_authentication_method = DemeAccount(username=slugify(name), agent=mike)
    mike_authentication_method.set_password('')
    permission2 = OneToOnePermission(source=mike, ability='do_anything', is_allowed=True)
    mike_authentication_method.save_versioned(action_agent=mike, initial_permissions=[permission2])
    Membership(item=mike, collection=discuss_group).save_versioned(action_agent=mike, initial_permissions=[OneToOnePermission(source=mike, ability='do_anything', is_allowed=True)])

