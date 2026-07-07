import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from './common/Button';
import { createProduct } from '../services/productWorkspaceService';

interface CreateProductModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const CreateProductModal: React.FC<CreateProductModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [titleZh, setTitleZh] = useState('');
  const [webappUrl, setWebappUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const reset = () => {
    setTitle('');
    setTitleZh('');
    setWebappUrl('');
    setError('');
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError('Product name is required');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await createProduct({
        title: title.trim(),
        title_zh: titleZh.trim() || undefined,
        webapp_url: webappUrl.trim() || undefined,
      });
      onSuccess();
      handleClose();
      navigate(`/products/${res.product.id}`);
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string } } };
      setError(ax.response?.data?.detail || (err instanceof Error ? err.message : 'Could not create product'));
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
        <div className="p-4 border-b">
          <h2 className="text-lg font-semibold">New product or service</h2>
          <p className="text-sm text-gray-500 mt-1">e.g. 5G Mobile Broadband, Postpaid Browse</p>
        </div>
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {error && <p className="text-red-600 text-sm">{error}</p>}
          <div>
            <label className="block text-sm font-medium mb-1">Name (English)</label>
            <input
              className="w-full border rounded px-3 py-2 text-sm"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="5G Mobile Broadband"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Name (中文) — optional</label>
            <input
              className="w-full border rounded px-3 py-2 text-sm"
              value={titleZh}
              onChange={(e) => setTitleZh(e.target.value)}
              placeholder="5G 流動寬頻"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">WebApp URL — optional</label>
            <input
              className="w-full border rounded px-3 py-2 text-sm"
              value={webappUrl}
              onChange={(e) => setWebappUrl(e.target.value)}
              placeholder="https://wwwuat.three.com.hk/..."
            />
            <p className="text-xs text-gray-500 mt-1">Used when generating browser tests. You can add later.</p>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" onClick={handleClose} disabled={loading}>Cancel</Button>
            <Button type="submit" disabled={loading}>{loading ? 'Creating…' : 'Create'}</Button>
          </div>
        </form>
      </div>
    </div>
  );
};
