"""
Django Models for Election Results
==================================
These models represent the database tables from the bincom_test.sql file.
"""

from django.db import models


class State(models.Model):
    """Nigerian States"""
    state_id = models.IntegerField(primary_key=True)
    state_name = models.CharField(max_length=50)

    class Meta:
        db_table = 'states'
        verbose_name_plural = 'States'
        managed = False

    def __str__(self):
        return self.state_name


class Lga(models.Model):
    """Local Government Areas"""
    uniqueid = models.AutoField(primary_key=True)
    lga_id = models.IntegerField()
    lga_name = models.CharField(max_length=50)
    state_id = models.IntegerField()
    lga_description = models.TextField(blank=True, null=True)
    entered_by_user = models.CharField(max_length=50, blank=True, null=True)
    date_entered = models.DateTimeField(blank=True, null=True)
    user_ip_address = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'lga'
        verbose_name = 'LGA'
        verbose_name_plural = 'LGAs'
        managed = False

    def __str__(self):
        return self.lga_name


class Ward(models.Model):
    """Electoral Wards"""
    uniqueid = models.AutoField(primary_key=True)
    ward_id = models.IntegerField()
    ward_name = models.CharField(max_length=50)
    lga_id = models.IntegerField()
    ward_description = models.TextField(blank=True, null=True)
    entered_by_user = models.CharField(max_length=50, blank=True, null=True)
    date_entered = models.DateTimeField(blank=True, null=True)
    user_ip_address = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'ward'
        managed = False

    def __str__(self):
        return self.ward_name


class PollingUnit(models.Model):
    """Polling Units"""
    uniqueid = models.AutoField(primary_key=True)
    polling_unit_id = models.IntegerField()
    ward_id = models.IntegerField()
    lga_id = models.IntegerField()
    uniquewardid = models.IntegerField(blank=True, null=True)
    polling_unit_number = models.CharField(max_length=50, blank=True, null=True)
    polling_unit_name = models.CharField(max_length=50, blank=True, null=True)
    polling_unit_description = models.TextField(blank=True, null=True)
    lat = models.CharField(max_length=255, blank=True, null=True)
    long = models.CharField(max_length=255, blank=True, null=True)
    entered_by_user = models.CharField(max_length=50, blank=True, null=True)
    date_entered = models.DateTimeField(blank=True, null=True)
    user_ip_address = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'polling_unit'
        verbose_name = 'Polling Unit'
        verbose_name_plural = 'Polling Units'
        managed = False

    def __str__(self):
        return self.polling_unit_name or f"PU {self.uniqueid}"


class Party(models.Model):
    """Political Parties"""
    id = models.AutoField(primary_key=True)
    partyid = models.CharField(max_length=11)
    partyname = models.CharField(max_length=11)

    class Meta:
        db_table = 'party'
        verbose_name_plural = 'Parties'
        managed = False

    def __str__(self):
        return self.partyname


class AnnouncedPuResults(models.Model):
    """Announced Polling Unit Results"""
    result_id = models.AutoField(primary_key=True)
    polling_unit_uniqueid = models.CharField(max_length=50)
    party_abbreviation = models.CharField(max_length=4)
    party_score = models.IntegerField()
    entered_by_user = models.CharField(max_length=50, blank=True, null=True)
    date_entered = models.DateTimeField(blank=True, null=True)
    user_ip_address = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'announced_pu_results'
        verbose_name = 'Polling Unit Result'
        verbose_name_plural = 'Polling Unit Results'

    def __str__(self):
        return f"PU {self.polling_unit_uniqueid} - {self.party_abbreviation}: {self.party_score}"


class AnnouncedLgaResults(models.Model):
    """Announced LGA Results (for comparison - not used in Q2 calculation)"""
    result_id = models.AutoField(primary_key=True)
    lga_name = models.CharField(max_length=50)
    party_abbreviation = models.CharField(max_length=4)
    party_score = models.IntegerField()
    entered_by_user = models.CharField(max_length=50, blank=True, null=True)
    date_entered = models.DateTimeField(blank=True, null=True)
    user_ip_address = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'announced_lga_results'
        verbose_name = 'LGA Result'
        verbose_name_plural = 'LGA Results'
        managed = False

    def __str__(self):
        return f"LGA {self.lga_name} - {self.party_abbreviation}: {self.party_score}"


class AgentName(models.Model):
    """Polling Agents"""
    name_id = models.AutoField(primary_key=True)
    firstname = models.CharField(max_length=255)
    lastname = models.CharField(max_length=255)
    email = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=13)
    pollingunit_uniqueid = models.IntegerField()

    class Meta:
        db_table = 'agentname'
        verbose_name = 'Agent'
        verbose_name_plural = 'Agents'
        managed = False

    def __str__(self):
        return f"{self.firstname} {self.lastname}"
