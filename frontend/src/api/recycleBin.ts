import client from './client';

export const recycleBinApi = {
  list: (params: { model: string; page?: number; page_size?: number }) =>
    client.get('/recycle-bin', { params }),

  summary: () =>
    client.get('/recycle-bin/summary'),

  restore: (model: string, id: number) =>
    client.put(`/recycle-bin/${model}/${id}/restore`),
};
