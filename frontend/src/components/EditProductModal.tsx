import React, { useEffect, useState } from 'react';
import { Button } from './common/Button';
import { getProduct, ProductDetail, updateProduct } from '../services/productWorkspaceService';

interface EditProductModalProps {
  productId: string;
  isOpen: boolean;
  onClose: () => void;
  onSaved: () => void;
}

export const EditProductModal: React.FC<EditProductModalProps> = ({
  productId,
  isOpen,
  onClose,
  onSaved,
}) => {
  const [title, setTitle] = useState('');
  const [titleZh, setTitleZh] = useState('');
  const [webappUrl, setWebappUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isOpen || !productId) return;
    getProduct(productId)
      .then((p: ProductDetail) => {
        setTitle(p.title);
        setTitleZh(p.title_zh || '');
        setWebappUrl(p.default_urls?.webapp || '');
      })
      .catch(() => setError('Could not load product'));
  }, [isOpen, productId]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await updateProduct(productId, {
        title: title.trim(),
        title_zh: titleZh.trim(),
        webapp_url: webappUrl.trim(),
      });
      onSaved();
      onClose();
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string } } };
      setError(ax.response?.data?.detail || 'Save failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
        <div className="p-4 border-b font-semibold">Product settings</div>
        <form onSubmit={handleSubmit} className="p-4 space-y-3">
          {error && <p className="text-red-600 text-sm">{error}</p>}
          <div>
            <label className="text-sm font-medium">Name (English)</label>
            <input className="w-full border rounded px-3 py-2 text-sm mt-1" value={title} onChange={(e) => setTitle(e.target.value)} required />
          </div>
          <div>
            <label className="text-sm font-medium">Name (中文)</label>
            <input className="w-full border rounded px-3 py-2 text-sm mt-1" value={titleZh} onChange={(e) => setTitleZh(e.target.value)} />
          </div>
          <div>
            <label className="text-sm font-medium">WebApp URL</label>
            <input className="w-full border rounded px-3 py-2 text-sm mt-1" value={webappUrl} onChange={(e) => setWebappUrl(e.target.value)} />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={loading}>{loading ? 'Saving…' : 'Save'}</Button>
          </div>
        </form>
      </div>
    </div>
  );
};
