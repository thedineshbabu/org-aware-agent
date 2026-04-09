import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "react-oidc-context";
import api from "../lib/api";

interface IngestResult {
  doc_name: string;
  chunks_inserted: number;
  message: string;
}

const ALLOWED_TYPES = [".pdf", ".docx", ".txt", ".md"];

export default function Ingest() {
  const auth = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [docName, setDocName] = useState("");
  const [section, setSection] = useState("");
  const [aclRoles, setAclRoles] = useState("employee");
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<IngestResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null;
    setFile(f);
    setResult(null);
    setError(null);
    if (f && !docName) {
      setDocName(f.name.replace(/\.[^.]+$/, ""));
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0] ?? null;
    if (f) {
      setFile(f);
      setResult(null);
      setError(null);
      if (!docName) setDocName(f.name.replace(/\.[^.]+$/, ""));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !auth.user?.access_token) return;

    setUploading(true);
    setError(null);
    setResult(null);

    const form = new FormData();
    form.append("file", file);
    form.append("doc_name", docName.trim());
    form.append("section", section.trim());
    form.append("acl_roles", aclRoles.trim() || "employee");

    try {
      const res = await api.post<IngestResult>("/api/v1/ingest", form, {
        headers: {
          Authorization: `Bearer ${auth.user.access_token}`,
          "Content-Type": "multipart/form-data",
        },
      });
      setResult(res.data);
      setFile(null);
      setDocName("");
      setSection("");
      if (fileInputRef.current) fileInputRef.current.value = "";
    } catch (err: unknown) {
      const body = (err as { response?: { data?: { detail?: string } } })?.response?.data;
      setError(body?.detail ?? (err instanceof Error ? err.message : "Upload failed."));
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to="/" className="text-gray-500 hover:text-gray-800 text-sm">
            ← Back to Chat
          </Link>
          <h1 className="text-lg font-semibold text-gray-900">Ingest Documents</h1>
        </div>
        <button
          onClick={() => auth.signoutRedirect()}
          className="text-sm text-gray-500 hover:text-gray-700 underline"
        >
          Sign out
        </button>
      </header>

      <main className="flex-1 overflow-y-auto p-6">
        <div className="max-w-2xl mx-auto space-y-6">

          {/* Success banner */}
          {result && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-green-800 font-medium">{result.message}</p>
              <p className="text-green-600 text-sm mt-1">
                {result.chunks_inserted} chunks stored for "{result.doc_name}"
              </p>
            </div>
          )}

          {/* Error banner */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-700">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-5">

            {/* Drop zone */}
            <div
              onDrop={handleDrop}
              onDragOver={(e) => e.preventDefault()}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
                ${file ? "border-blue-400 bg-blue-50" : "border-gray-300 hover:border-blue-400 hover:bg-gray-50"}`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.txt,.md"
                className="hidden"
                onChange={handleFileChange}
              />
              {file ? (
                <div>
                  <p className="text-blue-700 font-medium">{file.name}</p>
                  <p className="text-gray-500 text-sm mt-1">{(file.size / 1024).toFixed(1)} KB</p>
                </div>
              ) : (
                <div>
                  <p className="text-gray-600">Drop a file here or <span className="text-blue-600 underline">browse</span></p>
                  <p className="text-gray-400 text-sm mt-1">Supported: {ALLOWED_TYPES.join(", ")}</p>
                </div>
              )}
            </div>

            {/* Document name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Document Name
              </label>
              <input
                type="text"
                value={docName}
                onChange={(e) => setDocName(e.target.value)}
                placeholder="e.g. HR Handbook 2025"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Section */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Section <span className="text-gray-400 font-normal">(optional)</span>
              </label>
              <input
                type="text"
                value={section}
                onChange={(e) => setSection(e.target.value)}
                placeholder="e.g. Leave Policy"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* ACL Roles */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Access Roles
              </label>
              <input
                type="text"
                value={aclRoles}
                onChange={(e) => setAclRoles(e.target.value)}
                placeholder="employee,developer"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-gray-400 text-xs mt-1">Comma-separated roles that can search this document</p>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={!file || uploading}
              className="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 disabled:cursor-not-allowed
                         text-white text-sm font-medium rounded-lg transition-colors"
            >
              {uploading ? "Uploading…" : "Ingest Document"}
            </button>
          </form>

          {/* Help text */}
          <div className="text-sm text-gray-500 space-y-1">
            <p>Documents are split into chunks and stored in the knowledge base.</p>
            <p>Once ingested, the AI agent can find and cite them in chat responses.</p>
            <p>Maximum file size: 20 MB.</p>
          </div>
        </div>
      </main>
    </div>
  );
}
