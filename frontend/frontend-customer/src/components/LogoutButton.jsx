import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import { logout } from "../store/slices/authSlice";

const LogoutButton = ({children, className = ''}) => {
    const [isLogginOut, setIsLoggingOut] = useState(false);
    const dispatch = useDispatch();
    const navigate = useNavigate();
    const { user } = useSelector((state)=>state.auth);

    const handleLogout = async () =>{
        if (!user) return;

        setIsLoggingOut(true);

        try{
            await dispatch(logout());
            navigate('/login', {replace: true});
        }
        catch (error) {
            console.error('Logout failed:', error);

            //even when API call fails we should clear local state
            dispatch(logout());
            navigate('/login', {replace: true});
        }
        finally{
            setIsLoggingOut(false);
        }
    }

    return (
        <button onClick={handleLogout}
            disabled={isLogginOut}
            className={`${className}`}
            title = {`Logout ${user?.username || ''}`}
            >
                {isLogginOut ? 'Logging out...' : (children || 'Logout')}
        </button>
    );
};

export default LogoutButton;