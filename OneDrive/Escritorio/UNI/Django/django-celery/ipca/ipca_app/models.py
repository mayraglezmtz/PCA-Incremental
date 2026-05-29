from django.db import models

# Create your models here.
class DataModel(models.Model):
    f1 = models.FloatField()
    f2 = models.FloatField()
    f3 = models.FloatField()
    f4 = models.FloatField()
    f5 = models.FloatField()
    f6 = models.FloatField()
    f7 = models.FloatField()
    f8 = models.FloatField()
    f9 = models.FloatField()
    f10 = models.FloatField()

    pca_x = models.FloatField(null=True, blank=True)
    pca_y = models.FloatField(null=True, blank=True)

    promoted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"DataModel {self.id} - Promoted: {self.promoted}"
    
    def as_array(self):  #Convierte el objeto Django a un vector Python.
        """Returns the feature values as a list."""
        return [self.f1, self.f2, self.f3, self.f4, self.f5, self.f6, self.f7, self.f8, self.f9, self.f10]


DataPoint = DataModel
