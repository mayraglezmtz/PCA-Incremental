from unittest.mock import patch
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import DataPoint


def datapoint_payload(**overrides):
	payload = {
		"f1": 1.0,
		"f2": 2.0,
		"f3": 3.0,
		"f4": 4.0,
		"f5": 5.0,
		"f6": 6.0,
		"f7": 7.0,
		"f8": 8.0,
		"f9": 9.0,
		"f10": 10.0,
	}
	payload.update(overrides)
	return payload


class DataPointApiTests(APITestCase):
	def test_create_datapoint_returns_201_and_enqueues_training(self):
		url = reverse("datapoint-create")

		with patch("ipca_app.views.entrenar_pca_si_listo.delay") as mocked_delay:
			response = self.client.post(url, datapoint_payload(), format="json")

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(DataPoint.objects.count(), 1)
		mocked_delay.assert_called_once()

	def test_create_datapoint_ignores_read_only_fields(self):
		url = reverse("datapoint-create")
		payload = datapoint_payload(promoted=True, pca_x=99.0, pca_y=100.0)

		with patch("ipca_app.views.entrenar_pca_si_listo.delay"):
			response = self.client.post(url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		point = DataPoint.objects.get(pk=response.data["id"])
		self.assertFalse(point.promoted)
		self.assertIsNone(point.pca_x)
		self.assertIsNone(point.pca_y)

	def test_list_datapoints_returns_newest_first(self):
		older = DataPoint.objects.create(**datapoint_payload(f1=11.0))
		newer = DataPoint.objects.create(**datapoint_payload(f1=22.0))
		now = timezone.now()
		DataPoint.objects.filter(pk=older.pk).update(created_at=now - timedelta(minutes=1))
		DataPoint.objects.filter(pk=newer.pk).update(created_at=now)

		url = reverse("datapoint-list")
		response = self.client.get(url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data[0]["id"], newer.id)
		self.assertEqual(response.data[1]["id"], older.id)

	def test_update_promoted_datapoint_returns_403(self):
		point = DataPoint.objects.create(**datapoint_payload(), promoted=True)
		url = reverse("datapoint-detail", kwargs={"pk": point.pk})

		response = self.client.patch(url, {"f1": 123.0}, format="json")

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
		point.refresh_from_db()
		self.assertEqual(point.f1, 1.0)

	def test_delete_promoted_datapoint_returns_403(self):
		point = DataPoint.objects.create(**datapoint_payload(), promoted=True)
		url = reverse("datapoint-detail", kwargs={"pk": point.pk})

		response = self.client.delete(url)

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
		self.assertTrue(DataPoint.objects.filter(pk=point.pk).exists())

	def test_update_unpromoted_datapoint_succeeds(self):
		point = DataPoint.objects.create(**datapoint_payload())
		url = reverse("datapoint-detail", kwargs={"pk": point.pk})

		response = self.client.patch(url, {"f1": 123.0}, format="json")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		point.refresh_from_db()
		self.assertEqual(point.f1, 123.0)

	def test_delete_unpromoted_datapoint_succeeds(self):
		point = DataPoint.objects.create(**datapoint_payload())
		url = reverse("datapoint-detail", kwargs={"pk": point.pk})

		response = self.client.delete(url)

		self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
		self.assertFalse(DataPoint.objects.filter(pk=point.pk).exists())

	def test_coords_returns_400_for_unprocessed_datapoint(self):
		point = DataPoint.objects.create(**datapoint_payload(), promoted=False)
		url = reverse("datapoint-coords", kwargs={"pk": point.pk})

		response = self.client.get(url)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_coords_returns_200_for_processed_datapoint(self):
		point = DataPoint.objects.create(
			**datapoint_payload(),
			promoted=True,
			pca_x=1.23,
			pca_y=4.56,
		)
		url = reverse("datapoint-coords", kwargs={"pk": point.pk})

		response = self.client.get(url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["id"], point.id)
		self.assertEqual(response.data["pca_x"], 1.23)
		self.assertEqual(response.data["pca_y"], 4.56)

	def test_coords_returns_404_for_missing_datapoint(self):
		url = reverse("datapoint-coords", kwargs={"pk": 99999})

		response = self.client.get(url)

		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
