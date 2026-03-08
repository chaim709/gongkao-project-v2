export interface Package {
  id: number;
  name: string;
  description?: string;
  price: number;
  original_price?: number;
  validity_days: number;
  is_active: boolean;
  created_by?: number;
  created_at: string;
  updated_at?: string;
}

export interface PackageCreate {
  name: string;
  description?: string;
  price: number;
  original_price?: number;
  validity_days: number;
  is_active?: boolean;
}

export interface PackageItem {
  id: number;
  package_id: number;
  item_type: string;
  item_id: number;
  quantity: number;
  created_at: string;
}
