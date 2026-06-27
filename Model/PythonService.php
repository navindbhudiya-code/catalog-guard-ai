<?php
/**
 * Thin HTTP client to the CatalogGuard Python service.
 */

declare(strict_types=1);

namespace NavinDBhudiya\CatalogGuard\Model;

use Magento\Framework\App\Config\ScopeConfigInterface;
use Magento\Framework\HTTP\Client\Curl;
use Magento\Framework\Serialize\Serializer\Json;

class PythonService
{
    private const XML_PATH_BASE_URL = 'catalogguard/service/base_url';

    public function __construct(
        private readonly ScopeConfigInterface $scopeConfig,
        private readonly Curl $curl,
        private readonly Json $json
    ) {
    }

    public function getBaseUrl(): string
    {
        return rtrim((string) $this->scopeConfig->getValue(self::XML_PATH_BASE_URL), '/');
    }

    /**
     * Trigger an audit run on the Python service and return the decoded summary.
     *
     * @return array<string, mixed>
     */
    public function runAudit(string $checks = 'sanity,attributes,duplicates,seo'): array
    {
        $this->curl->addHeader('Content-Type', 'application/json');
        $this->curl->post(
            $this->getBaseUrl() . '/audit',
            $this->json->serialize(['checks' => $checks])
        );

        return $this->decode($this->curl->getBody());
    }

    /**
     * Fetch the latest audit report from the Python service.
     *
     * @return array<string, mixed>
     */
    public function getLatestReport(): array
    {
        $this->curl->get($this->getBaseUrl() . '/report/latest');

        return $this->decode($this->curl->getBody());
    }

    /**
     * Fetch a page of pending fix proposals for the review grid.
     *
     * @return array{items: array<int, array<string, mixed>>, totalRecords: int}
     */
    public function getPendingProposals(int $page = 1, int $limit = 50): array
    {
        $this->curl->get($this->getBaseUrl() . '/proposals?page=' . $page . '&limit=' . $limit);
        $data = $this->decode($this->curl->getBody());

        return [
            'items' => is_array($data['items'] ?? null) ? $data['items'] : [],
            'totalRecords' => (int) ($data['totalRecords'] ?? 0),
        ];
    }

    /**
     * Run an audit and generate fix proposals into the review queue.
     */
    public function generateProposals(string $checks = 'sanity,attributes,duplicates,seo'): int
    {
        $this->curl->addHeader('Content-Type', 'application/json');
        $this->curl->post(
            $this->getBaseUrl() . '/propose',
            $this->json->serialize(['checks' => $checks])
        );

        return (int) ($this->decode($this->curl->getBody())['generated'] ?? 0);
    }

    /**
     * Apply all APPROVED fixes to the store (journaled for rollback).
     *
     * @return array{success: bool, applied: int, batch: string, message: string}
     */
    public function applyApproved(): array
    {
        $this->curl->addHeader('Content-Type', 'application/json');
        $this->curl->post($this->getBaseUrl() . '/apply', '{}');
        $data = $this->decode($this->curl->getBody());

        return [
            'success' => (bool) ($data['success'] ?? false),
            'applied' => (int) ($data['applied'] ?? 0),
            'batch' => (string) ($data['batch_id'] ?? ''),
            'message' => (string) ($data['message'] ?? ''),
        ];
    }

    /**
     * Roll back the most recent applied batch.
     *
     * @return array{success: bool, reverted: int, message: string}
     */
    public function rollbackLast(): array
    {
        $this->curl->addHeader('Content-Type', 'application/json');
        $this->curl->post($this->getBaseUrl() . '/rollback', '{}');
        $data = $this->decode($this->curl->getBody());

        return [
            'success' => (bool) ($data['success'] ?? false),
            'reverted' => (int) ($data['reverted'] ?? 0),
            'message' => (string) ($data['message'] ?? ''),
        ];
    }

    public function approveProposal(string $id): bool
    {
        return $this->postAction('/api/proposals/' . rawurlencode($id) . '/approve');
    }

    public function rejectProposal(string $id): bool
    {
        return $this->postAction('/api/proposals/' . rawurlencode($id) . '/reject');
    }

    private function postAction(string $path): bool
    {
        $this->curl->addHeader('Content-Type', 'application/json');
        $this->curl->post($this->getBaseUrl() . $path, '{}');
        $data = $this->decode($this->curl->getBody());

        return (bool) ($data['success'] ?? false);
    }

    /**
     * @return array<string, mixed>
     */
    private function decode(string $body): array
    {
        if ($body === '') {
            return [];
        }

        $decoded = $this->json->unserialize($body);

        return is_array($decoded) ? $decoded : [];
    }
}
