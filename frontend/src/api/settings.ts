import client from './client';
import type { ShiyeTierThresholdSettings } from '../types/settings';

export const settingsApi = {
  getShiyeTierThresholds: () =>
    client.get<any, ShiyeTierThresholdSettings>('/settings/shiye-tier-thresholds'),

  updateShiyeTierThresholds: (data: ShiyeTierThresholdSettings) =>
    client.put<ShiyeTierThresholdSettings, ShiyeTierThresholdSettings>(
      '/settings/shiye-tier-thresholds',
      data,
    ),
};
