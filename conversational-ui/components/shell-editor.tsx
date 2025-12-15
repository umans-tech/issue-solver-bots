'use client';

import React, { useEffect, useRef } from 'react';
import { EditorState, Transaction } from '@codemirror/state';
import { EditorView } from '@codemirror/view';
import { basicSetup } from 'codemirror';
import { oneDark } from '@codemirror/theme-one-dark';
import { StreamLanguage } from '@codemirror/language';
import { shell } from '@codemirror/legacy-modes/mode/shell';

interface ShellEditorProps {
  value: string;
  onChange: (next: string) => void;
  minHeight?: number;
  placeholder?: string;
  forceSetValue?: boolean;
}

export function ShellEditor({
  value,
  onChange,
  minHeight = 160,
  placeholder,
  forceSetValue = false,
}: ShellEditorProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const viewRef = useRef<EditorView | null>(null);

  useEffect(() => {
    if (!containerRef.current || viewRef.current) return;

    const startState = EditorState.create({
      doc: value,
      extensions: [
        basicSetup,
        oneDark,
        StreamLanguage.define(shell),
        EditorView.lineWrapping,
        EditorView.updateListener.of((update) => {
          if (update.docChanged) {
            const tr = update.transactions.find(
              (t) => !t.annotation(Transaction.remote),
            );
            if (tr) onChange(update.state.doc.toString());
          }
        }),
        EditorView.theme({
          '&': {
            width: '100%',
            minHeight: `${minHeight}px`,
            border: '1px solid var(--border)',
            borderRadius: '0.5rem',
          },
          '.cm-scroller': {
            fontFamily:
              'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
            fontSize: '0.85rem',
          },
          '.cm-content': { padding: '12px' },
          '.cm-gutters': { borderRight: '1px solid var(--border)' },
        }),
      ],
    });

    viewRef.current = new EditorView({
      state: startState,
      parent: containerRef.current,
    });

    return () => {
      viewRef.current?.destroy();
      viewRef.current = null;
    };
    // We intentionally run this only once to avoid tearing/caret jumps
    // caused by re-creating the editor on each value change.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!viewRef.current) return;
    if (!forceSetValue) return;
    const current = viewRef.current.state.doc.toString();
    if (current === value) return;
    const end = value.length;
    const tr = viewRef.current.state.update({
      changes: { from: 0, to: current.length, insert: value },
      selection: { anchor: end },
      annotations: [Transaction.remote.of(true)],
    });
    viewRef.current.dispatch(tr);
  }, [value, forceSetValue]);

  return (
    <div className="w-full">
      {placeholder && !value && (
        <div className="text-xs text-muted-foreground mb-1">{placeholder}</div>
      )}
      <div ref={containerRef} />
    </div>
  );
}
