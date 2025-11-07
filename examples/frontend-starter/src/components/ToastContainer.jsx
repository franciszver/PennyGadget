import Toast from './Toast';
import './ToastContainer.css';

function ToastContainer({ toasts, onRemove }) {
  return (
    <div className="toast-container">
      {toasts.map(toast => (
        <Toast
          key={toast.id}
          message={toast.message}
          type={toast.type}
          onClose={() => onRemove(toast.id)}
          duration={0} // Manual close only when in container
        />
      ))}
    </div>
  );
}

export default ToastContainer;

