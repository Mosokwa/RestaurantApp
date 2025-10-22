import Navigation from './Navigation';
import Footer from "./Footer";
import { Outlet } from "react-router-dom";
import "./Layout.css"

const Layout = () =>{
    return (
        <div className="layout">
            <header className="layout-header">
                <Navigation/>
            </header>
            <main className="main-content">
                <Outlet/>
            </main>
            <footer>
                <Footer/>
            </footer>
        </div>
    );
};

export default Layout;