import client from './client';
import type { Package } from '../types/package';

export const packageApi = {
  listPackages: (params: { page: number; page_size: number; is_active?: boolean }) =>
    client.get('/packages', { params }).then((res) => res.data),

  createPackage: (data: Partial<Package>) =>
    client.post('/packages', data).then((res) => res.data),

  updatePackage: (id: number, data: Partial<Package>) =>
    client.put(`/packages/${id}`, data).then((res) => res.data),

  deletePackage: (id: number) =>
    client.delete(`/packages/${id}`),

  listPackageItems: (packageId: number) =>
    client.get(`/packages/${packageId}/items`).then((res) => res.data),

  addPackageItem: (packageId: number, data: any) =>
    client.post(`/packages/${packageId}/items`, data).then((res) => res.data),

  removePackageItem: (itemId: number) =>
    client.delete(`/package-items/${itemId}`),
};
