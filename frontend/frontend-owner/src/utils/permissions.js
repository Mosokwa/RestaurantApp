// Permission levels and checks
export const PERMISSION_LEVELS = {
  OWNER: 'owner',
  MANAGER: 'manager',
  KITCHEN: 'kitchen',
  DELIVERY: 'delivery',
  CASHIER: 'cashier'
};

export const hasPermission = (user, permission, restaurantId = null) => {
  if (!user) return false;

  // Owners have all permissions for their restaurants
  if (user.user_type === 'owner') {
    return true;
  }

  // Staff permissions
  if (user.user_type === 'staff' && user.staff_profile) {
    const staff = user.staff_profile;
    
    // Check if staff has access to this restaurant
    if (restaurantId && staff.restaurant.restaurant_id !== restaurantId) {
      return false;
    }

    // Check branch access if specified
    // if (branchId && !staff.branch_access.includes(branchId)) {
    //   return false;
    // }

    // Check specific permissions
    switch (permission) {
      case 'view_reports':
        return staff.can_view_reports;
      case 'manage_menu':
        return staff.can_manage_menu;
      case 'manage_orders':
        return staff.can_manage_orders;
      case 'manage_staff':
        return staff.can_manage_staff;
      case 'access_kitchen':
        return staff.role === 'chef' || staff.role === 'manager';
      case 'process_payments':
        return staff.role === 'cashier' || staff.role === 'manager';
      default:
        return false;
    }
  }

  return false;
};

export const canAccessRoute = (user, route) => {
  const routePermissions = {
    '/owner/dashboard': ['owner', 'manager'],
    '/owner/reports': ['owner', 'manager'],
    '/owner/staff': ['owner', 'manager'],
    '/owner/menu': ['owner', 'manager'],
    '/kitchen/orders': ['owner', 'manager', 'kitchen'],
    '/cashier/pos': ['owner', 'manager', 'cashier']
  };

  if (!user || !routePermissions[route]) return false;

  return routePermissions[route].includes(
    user.user_type === 'owner' ? 'owner' : user.staff_profile?.role
  );
};