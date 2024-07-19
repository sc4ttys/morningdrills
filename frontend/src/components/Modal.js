import React from 'react';
import ReactDOM from 'react-dom';

const Modal = ({ isShowing, hide, children }) => {
  if (!isShowing) {
    return null;
  }

  return ReactDOM.createPortal(
    <div className="modal-overlay">
      <div className="modal">
        <button className="modal-close" onClick={hide}>
          &times;
        </button>
        {children}
      </div>
    </div>,
    document.body
  );
};

export default Modal;
