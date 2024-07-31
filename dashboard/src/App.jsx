// App.jsx
import "./App.css";
import Dashboard from "./Dashboard";

import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

const App = () => {
  return (
    <Router>
      <div className="app">
        <div className="app-body">
          {/* <Sidebar /> */}
          <div className="main-content">
            <Routes>
              <Route exact path="/" element={<Dashboard />} />
            </Routes>
          </div>
        </div>
      </div>
    </Router>
  );
};

export default App;
